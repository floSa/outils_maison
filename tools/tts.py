"""Synthèse vocale locale (« lire un texte à voix haute »).

S'appuie sur **Kokoro** (modèle open-source, Apache-2.0) via `kokoro-onnx`, qui
tourne sur CPU (ou GPU) avec `onnxruntime` — **sans PyTorch**. La phonémisation
française passe par espeak-ng, embarqué par `espeakng-loader` (aucune
installation système requise).

Principe habituel du projet : **logique pure ici, UI dans `pages/`**. Les imports
lourds (`kokoro_onnx`, `onnxruntime`, `numpy`) restent internes aux fonctions
pour que le simple rendu des pages ne les charge pas.

Le modèle (~340 Mo) n'est pas versionné : il est téléchargé une fois au premier
usage, comme le navigateur Playwright. Il est mis en cache hors du dépôt
(``~/.cache/outils_maison/kokoro`` par défaut, surchargeable via la variable
d'environnement ``OUTILS_TTS_DIR``).
"""

from __future__ import annotations

import io
import os
import re
import wave
from pathlib import Path
from typing import Callable

# Voix proposées : libellé lisible -> (identifiant Kokoro, code langue espeak).
# Le français (une seule voix chez Kokoro) est en tête ; les autres lisent au
# mieux dans **leur** langue (un texte français lu par une voix anglaise sera
# phonémisé à l'anglaise).
VOIX: dict[str, tuple[str, str]] = {
    "Français — Siwis (femme)": ("ff_siwis", "fr-fr"),
    "Anglais US — Heart (femme)": ("af_heart", "en-us"),
    "Anglais US — Michael (homme)": ("am_michael", "en-us"),
    "Anglais GB — George (homme)": ("bm_george", "en-gb"),
    "Espagnol — Dora (femme)": ("ef_dora", "es"),
    "Italien — Sara (femme)": ("if_sara", "it"),
    "Portugais BR — Santa (femme)": ("pf_dora", "pt-br"),
}

# Fréquence d'échantillonnage du modèle Kokoro.
FREQUENCE_HZ = 24_000

# Fichiers du modèle : (url, nom de fichier, taille approx. en octets — pour la
# barre de progression uniquement).
_RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
_FICHIERS: tuple[tuple[str, str, int], ...] = (
    (f"{_RELEASE}/kokoro-v1.0.onnx", "kokoro-v1.0.onnx", 310_000_000),
    (f"{_RELEASE}/voices-v1.0.bin", "voices-v1.0.bin", 27_000_000),
)


# --------------------------------------------------------------------------- #
# Emplacement et présence du modèle
# --------------------------------------------------------------------------- #


def dossier_modele() -> Path:
    """Dossier de cache du modèle (créé au besoin)."""
    base = os.environ.get("OUTILS_TTS_DIR")
    dossier = Path(base) if base else Path.home() / ".cache" / "outils_maison" / "kokoro"
    dossier.mkdir(parents=True, exist_ok=True)
    return dossier


def chemins_modele() -> tuple[Path, Path]:
    """Chemins (onnx, voix) attendus dans le cache."""
    dossier = dossier_modele()
    return dossier / _FICHIERS[0][1], dossier / _FICHIERS[1][1]


def modele_present() -> bool:
    """Vrai si les deux fichiers du modèle sont déjà téléchargés."""
    return all(chemin.is_file() for chemin in chemins_modele())


def telecharger_modele(progression: Callable[[float, str], None] | None = None) -> None:
    """Télécharge les fichiers manquants du modèle.

    :param progression: rappel optionnel ``(fraction_globale, libellé)`` appelé
        pendant le téléchargement (``fraction_globale`` entre 0 et 1).
    """
    import urllib.request

    dossier = dossier_modele()
    a_faire = [
        (url, dossier / nom, taille)
        for url, nom, taille in _FICHIERS
        if not (dossier / nom).is_file()
    ]
    total = sum(taille for _, _, taille in a_faire) or 1
    deja = 0

    for url, cible, taille in a_faire:
        temporaire = cible.with_suffix(cible.suffix + ".part")
        with urllib.request.urlopen(url) as reponse, open(temporaire, "wb") as sortie:
            attendu = int(reponse.headers.get("Content-Length") or taille)
            lu = 0
            while True:
                bloc = reponse.read(1 << 20)  # 1 Mo
                if not bloc:
                    break
                sortie.write(bloc)
                lu += len(bloc)
                if progression:
                    fraction = (deja + min(lu, attendu)) / total
                    progression(min(fraction, 1.0), cible.name)
        temporaire.replace(cible)
        deja += taille

    if progression:
        progression(1.0, "terminé")


# --------------------------------------------------------------------------- #
# Matériel disponible (CPU / GPU)
# --------------------------------------------------------------------------- #


def providers_disponibles() -> list[str]:
    """Liste des « execution providers » onnxruntime disponibles."""
    import onnxruntime

    return list(onnxruntime.get_available_providers())


def gpu_disponible() -> bool:
    """Vrai si un provider GPU (CUDA/ROCm/DirectML) est utilisable."""
    return any(
        p in providers_disponibles()
        for p in ("CUDAExecutionProvider", "ROCMExecutionProvider", "DmlExecutionProvider")
    )


# --------------------------------------------------------------------------- #
# Découpage du texte
# --------------------------------------------------------------------------- #


def decouper_texte(texte: str, max_car: int = 1500) -> list[str]:
    """Découpe un texte en morceaux ``<= max_car`` (paragraphes, puis phrases).

    Les longs textes sont synthétisés morceau par morceau puis recollés : cela
    évite les limites internes du modèle et donne une progression lisible.
    """
    texte = texte.strip()
    if not texte:
        return []

    morceaux: list[str] = []
    for para in re.split(r"\n\s*\n", texte):
        para = " ".join(para.split())
        if not para:
            continue
        if len(para) <= max_car:
            morceaux.append(para)
            continue
        courant = ""
        for phrase in re.split(r"(?<=[.!?…])\s+", para):
            if len(courant) + len(phrase) + 1 <= max_car:
                courant = f"{courant} {phrase}".strip()
            else:
                if courant:
                    morceaux.append(courant)
                if len(phrase) <= max_car:
                    courant = phrase
                else:  # phrase seule trop longue : coupe brute
                    for i in range(0, len(phrase), max_car):
                        morceaux.append(phrase[i : i + max_car])
                    courant = ""
        if courant:
            morceaux.append(courant)
    return morceaux


# --------------------------------------------------------------------------- #
# Encodage WAV (sans dépendance supplémentaire)
# --------------------------------------------------------------------------- #


def _encoder_wav(samples, frequence: int = FREQUENCE_HZ) -> bytes:
    """Convertit un tableau flottant [-1, 1] en WAV PCM 16 bits mono."""
    import numpy as np

    pcm = np.clip(np.asarray(samples, dtype=np.float32), -1.0, 1.0)
    pcm16 = (pcm * 32767.0).astype("<i2")
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(frequence)
        w.writeframes(pcm16.tobytes())
    return tampon.getvalue()


# --------------------------------------------------------------------------- #
# Synthèse
# --------------------------------------------------------------------------- #

_moteurs: dict[bool, object] = {}


def _charger_kokoro(gpu: bool):
    """Charge (et met en cache) le moteur Kokoro pour le matériel demandé."""
    if gpu not in _moteurs:
        # kokoro-onnx choisit son provider via cette variable d'environnement,
        # lue à la construction de la session onnxruntime.
        os.environ["ONNX_PROVIDER"] = (
            "CUDAExecutionProvider" if gpu else "CPUExecutionProvider"
        )
        from kokoro_onnx import Kokoro

        onnx, voix = chemins_modele()
        _moteurs[gpu] = Kokoro(str(onnx), str(voix))
    return _moteurs[gpu]


def synthetiser(
    texte: str,
    voix: str = "ff_siwis",
    lang: str = "fr-fr",
    vitesse: float = 1.0,
    gpu: bool = False,
) -> bytes:
    """Synthétise ``texte`` et renvoie un WAV (octets).

    :param voix: identifiant Kokoro (voir :data:`VOIX`).
    :param lang: code langue espeak (``fr-fr``, ``en-us``…).
    :param vitesse: 0.5 (lent) à 2.0 (rapide), 1.0 = normal.
    :param gpu: utilise le provider GPU si disponible.
    :raises FileNotFoundError: si le modèle n'est pas téléchargé.
    :raises ValueError: si le texte est vide.
    """
    if not modele_present():
        raise FileNotFoundError(
            "Modèle de synthèse absent : lancez telecharger_modele() d'abord."
        )
    morceaux = decouper_texte(texte)
    if not morceaux:
        raise ValueError("Texte vide.")

    import numpy as np

    moteur = _charger_kokoro(gpu)
    silence = np.zeros(int(FREQUENCE_HZ * 0.3), dtype=np.float32)  # 0,3 s entre blocs
    parties: list = []
    for i, morceau in enumerate(morceaux):
        samples, _ = moteur.create(morceau, voice=voix, speed=float(vitesse), lang=lang)
        if i:
            parties.append(silence)
        parties.append(np.asarray(samples, dtype=np.float32))

    return _encoder_wav(np.concatenate(parties))
