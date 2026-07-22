"""Transcription audio/vidéo → texte (« transcrire un enregistrement »).

S'appuie sur **Whisper** (OpenAI) exécuté par **faster-whisper** sur CTranslate2,
sur CPU (ou GPU) — **sans PyTorch**. `av` (PyAV) embarque ffmpeg et décode
directement l'audio **et** la vidéo. Whisper détecte la langue, gère les longs
fichiers (fenêtrage interne + VAD) et fournit des segments horodatés → sous-titres.

Même principe que le reste du projet : **logique pure ici, UI dans `pages/`**. Les
imports lourds (`faster_whisper`) restent internes aux fonctions.

Le modèle n'est pas versionné : il est téléchargé une fois au premier usage, dans
``~/.cache/outils_maison/whisper`` par défaut — surchargeable via la variable
d'environnement ``OUTILS_TRANSCRIPTION_DIR``.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

# Modèles proposés : libellé -> nom faster-whisper. Le turbo est le défaut
# (qualité quasi maximale, nettement plus rapide que large-v3 sur CPU).
MODELES: dict[str, str] = {
    "large-v3-turbo (recommandé)": "large-v3-turbo",
    "medium": "medium",
    "small (rapide)": "small",
    "large-v3 (qualité max)": "large-v3",
}

# Langues : libellé -> code Whisper (None = détection automatique).
LANGUES: dict[str, str | None] = {
    "Détection automatique": None,
    "Français": "fr",
    "Anglais": "en",
    "Espagnol": "es",
    "Allemand": "de",
    "Italien": "it",
    "Portugais": "pt",
    "Néerlandais": "nl",
    "Russe": "ru",
    "Arabe": "ar",
    "Chinois": "zh",
    "Japonais": "ja",
}


# --------------------------------------------------------------------------- #
# Emplacement du modèle / matériel
# --------------------------------------------------------------------------- #


def dossier_modele() -> Path:
    """Dossier de cache des modèles Whisper (créé au besoin)."""
    base = os.environ.get("OUTILS_TRANSCRIPTION_DIR")
    dossier = Path(base) if base else Path.home() / ".cache" / "outils_maison" / "whisper"
    dossier.mkdir(parents=True, exist_ok=True)
    return dossier


def gpu_disponible() -> bool:
    """Vrai si CTranslate2 voit un GPU CUDA utilisable."""
    import ctranslate2

    try:
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:  # noqa: BLE001 — pas de CUDA compilé, etc.
        return False


# --------------------------------------------------------------------------- #
# Sous-titres (SRT / VTT) — fonctions pures
# --------------------------------------------------------------------------- #


def _horodatage(secondes: float, vtt: bool = False) -> str:
    """Formate un temps en ``HH:MM:SS,mmm`` (SRT) ou ``HH:MM:SS.mmm`` (VTT)."""
    secondes = max(0.0, secondes)
    heures, reste = divmod(int(secondes), 3600)
    minutes, sec = divmod(reste, 60)
    milli = int(round((secondes - int(secondes)) * 1000))
    sep = "." if vtt else ","
    return f"{heures:02d}:{minutes:02d}:{sec:02d}{sep}{milli:03d}"


def generer_srt(segments: list[dict]) -> str:
    """Construit un fichier SRT à partir de segments ``{debut, fin, texte}``."""
    blocs = []
    for i, seg in enumerate(segments, start=1):
        debut = _horodatage(seg["debut"])
        fin = _horodatage(seg["fin"])
        blocs.append(f"{i}\n{debut} --> {fin}\n{seg['texte'].strip()}\n")
    return "\n".join(blocs)


def generer_vtt(segments: list[dict]) -> str:
    """Construit un fichier WebVTT à partir de segments ``{debut, fin, texte}``."""
    lignes = ["WEBVTT", ""]
    for seg in segments:
        debut = _horodatage(seg["debut"], vtt=True)
        fin = _horodatage(seg["fin"], vtt=True)
        lignes.append(f"{debut} --> {fin}")
        lignes.append(seg["texte"].strip())
        lignes.append("")
    return "\n".join(lignes)


# --------------------------------------------------------------------------- #
# Transcription
# --------------------------------------------------------------------------- #

_moteurs: dict[tuple[str, bool], object] = {}


def _charger(modele: str, gpu: bool):
    """Charge (et met en cache) le modèle Whisper pour le matériel demandé."""
    cle = (modele, gpu)
    if cle not in _moteurs:
        from faster_whisper import WhisperModel

        _moteurs[cle] = WhisperModel(
            modele,
            device="cuda" if gpu else "cpu",
            compute_type="float16" if gpu else "int8",
            download_root=str(dossier_modele()),
        )
    return _moteurs[cle]


def transcrire(
    chemin: str | Path,
    modele: str = "large-v3-turbo",
    langue: str | None = None,
    gpu: bool = False,
    vad: bool = True,
    progression: Callable[[float], None] | None = None,
) -> dict:
    """Transcrit un fichier audio ou vidéo.

    :param modele: nom faster-whisper (cf. :data:`MODELES`).
    :param langue: code Whisper (``fr``…) ou ``None`` pour la détection auto.
    :param gpu: utilise le GPU CUDA si disponible.
    :param vad: filtre les silences (améliore qualité et vitesse).
    :param progression: rappel optionnel ``(fraction)`` (0 à 1) par segment.
    :return: ``{"texte", "segments", "langue", "duree"}`` ; chaque segment est
        ``{"debut", "fin", "texte"}``.
    :raises FileNotFoundError: si le fichier n'existe pas.
    """
    chemin = Path(chemin)
    if not chemin.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    modele_charge = _charger(modele, gpu)
    iterateur, info = modele_charge.transcribe(
        str(chemin), language=langue, vad_filter=vad, beam_size=5
    )

    segments: list[dict] = []
    for seg in iterateur:
        segments.append({"debut": seg.start, "fin": seg.end, "texte": seg.text.strip()})
        if progression and info.duration:
            progression(min(seg.end / info.duration, 1.0))

    if progression:
        progression(1.0)

    return {
        "texte": " ".join(s["texte"] for s in segments).strip(),
        "segments": segments,
        "langue": info.language,
        "duree": info.duration,
    }
