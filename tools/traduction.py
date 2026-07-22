"""Traduction hors-ligne (« traduire un texte »).

S'appuie sur **NLLB-200 distillé 600M** (Meta, CC-BY-NC) exécuté par **CTranslate2**
sur CPU (ou GPU) — **sans PyTorch**. `ctranslate2` fait l'inférence ; `transformers`
ne sert que de **tokenizer** (aucune dépendance torch). Un seul modèle (~600 Mo,
quantifié int8) couvre **200 langues**.

Même principe que le reste du projet : **logique pure ici, UI dans `pages/`**. Les
imports lourds (`ctranslate2`, `transformers`) restent internes aux fonctions.

Le modèle n'est pas versionné : il est téléchargé une fois au premier usage (comme
la synthèse vocale), dans ``~/.cache/outils_maison/nllb`` par défaut — surchargeable
via la variable d'environnement ``OUTILS_TRADUCTION_DIR``.

Alternatives possibles (voir la doc) : OPUS-MT par paire (plus léger si peu de
langues) ou NLLB-200 1.3B (meilleure qualité, plus lourd).
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable

# Dépôt HuggingFace du modèle NLLB déjà converti en CTranslate2 (int8, ~623 Mo),
# auto-suffisant (modèle + tokenizer inclus → chargement hors-ligne).
REPO = "JustFrederik/nllb-200-distilled-600M-ct2-int8"

# Langues proposées : libellé français -> code FLORES-200 (attendu par NLLB).
# L'anglais et le français sont en tête (cas d'usage principal : EN -> FR).
LANGUES: dict[str, str] = {
    "Anglais": "eng_Latn",
    "Français": "fra_Latn",
    "Espagnol": "spa_Latn",
    "Allemand": "deu_Latn",
    "Italien": "ita_Latn",
    "Portugais": "por_Latn",
    "Néerlandais": "nld_Latn",
    "Russe": "rus_Cyrl",
    "Arabe": "arb_Arab",
    "Chinois (simplifié)": "zho_Hans",
    "Japonais": "jpn_Jpan",
    "Coréen": "kor_Hang",
    "Polonais": "pol_Latn",
    "Turc": "tur_Latn",
    "Ukrainien": "ukr_Cyrl",
}

# Fichiers indispensables au chargement hors-ligne (présence = modèle prêt).
_FICHIERS_REQUIS = ("model.bin", "sentencepiece.bpe.model", "tokenizer_config.json")


# --------------------------------------------------------------------------- #
# Emplacement et présence du modèle
# --------------------------------------------------------------------------- #


def dossier_modele() -> Path:
    """Dossier de cache du modèle (créé au besoin)."""
    base = os.environ.get("OUTILS_TRADUCTION_DIR")
    dossier = Path(base) if base else Path.home() / ".cache" / "outils_maison" / "nllb"
    dossier.mkdir(parents=True, exist_ok=True)
    return dossier


def modele_present() -> bool:
    """Vrai si le modèle (et son tokenizer) est déjà téléchargé."""
    dossier = dossier_modele()
    return all((dossier / nom).is_file() for nom in _FICHIERS_REQUIS)


def telecharger_modele(progression: Callable[[float, str], None] | None = None) -> None:
    """Télécharge le modèle NLLB (fichiers manquants uniquement).

    :param progression: rappel optionnel ``(fraction_globale, libellé)`` (0 à 1).
    """
    import urllib.request

    from huggingface_hub import HfApi

    dossier = dossier_modele()
    info = HfApi().model_info(REPO, files_metadata=True)
    fichiers = [
        (s.rfilename, s.size or 0)
        for s in info.siblings
        if not s.rfilename.startswith(".")
        and s.rfilename not in ("README.md", "LICENSE.model.md")
    ]
    total = sum(taille for _, taille in fichiers) or 1
    deja = 0

    for nom, taille in fichiers:
        cible = dossier / nom
        if cible.is_file() and taille and cible.stat().st_size == taille:
            deja += taille
            continue
        url = f"https://huggingface.co/{REPO}/resolve/main/{nom}"
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
                    progression(min(fraction, 1.0), nom)
        temporaire.replace(cible)
        deja += taille

    if progression:
        progression(1.0, "terminé")


# --------------------------------------------------------------------------- #
# Matériel disponible (CPU / GPU)
# --------------------------------------------------------------------------- #


def gpu_disponible() -> bool:
    """Vrai si CTranslate2 voit un GPU CUDA utilisable."""
    import ctranslate2

    try:
        return ctranslate2.get_cuda_device_count() > 0
    except Exception:  # noqa: BLE001 — pas de CUDA compilé, etc.
        return False


# --------------------------------------------------------------------------- #
# Découpage du texte
# --------------------------------------------------------------------------- #


def decouper_texte(texte: str, max_car: int = 1000) -> list[str]:
    """Découpe un texte en morceaux ``<= max_car`` (paragraphes, puis phrases).

    NLLB traduit par segment ; on découpe pour éviter la troncature des longs
    passages et garder une traduction phrase à phrase cohérente.
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
# Traduction
# --------------------------------------------------------------------------- #

_moteurs: dict[bool, tuple] = {}


def _charger(gpu: bool):
    """Charge (et met en cache) le traducteur CTranslate2 + son tokenizer."""
    if gpu not in _moteurs:
        import ctranslate2
        import transformers

        # Le tokenizer NLLB (SentencePiece) déclenche des avertissements génériques
        # de transformers 5.x sans incidence sur la sortie ; on réduit le bruit.
        transformers.logging.set_verbosity_error()
        chemin = str(dossier_modele())
        translator = ctranslate2.Translator(chemin, device="cuda" if gpu else "cpu")
        tokenizer = transformers.AutoTokenizer.from_pretrained(chemin)
        _moteurs[gpu] = (translator, tokenizer)
    return _moteurs[gpu]


def _preparer_lignes(texte: str) -> tuple[list[str], list[str], list[list[int]]]:
    """Prépare une traduction **ligne par ligne** (préserve la mise en page).

    Retourne ``(lignes, morceaux, plan)`` : ``morceaux`` est la liste à plat des
    segments à traduire ; ``plan[i]`` donne les indices des morceaux de la ligne
    ``i`` (liste vide pour une ligne vide). Reconstruire avec :func:`_reconstituer`.
    """
    lignes = texte.split("\n")
    morceaux: list[str] = []
    plan: list[list[int]] = []
    for ligne in lignes:
        if not ligne.strip():  # ligne vide : préservée telle quelle
            plan.append([])
            continue
        indices = []
        for m in decouper_texte(ligne):  # découpe une ligne très longue
            indices.append(len(morceaux))
            morceaux.append(m)
        plan.append(indices)
    return lignes, morceaux, plan


def _reconstituer(plan: list[list[int]], traduits: list[str]) -> str:
    """Recolle les morceaux traduits **en préservant les sauts de ligne** d'origine."""
    return "\n".join(
        " ".join(traduits[i] for i in indices) if indices else ""
        for indices in plan
    )


def traduire(texte: str, source: str, cible: str, gpu: bool = False) -> str:
    """Traduit ``texte`` de la langue ``source`` vers ``cible`` (codes FLORES-200).

    La **mise en page** (retours à la ligne, lignes vides) est préservée : la
    traduction se fait ligne par ligne.

    :param source: code langue source, ex. ``eng_Latn`` (cf. :data:`LANGUES`).
    :param cible: code langue cible, ex. ``fra_Latn``.
    :param gpu: utilise le GPU CUDA si disponible.
    :raises FileNotFoundError: si le modèle n'est pas téléchargé.
    """
    if not modele_present():
        raise FileNotFoundError(
            "Modèle de traduction absent : lancez telecharger_modele() d'abord."
        )
    if source == cible or not texte.strip():
        return texte

    lignes, morceaux, plan = _preparer_lignes(texte)
    if not morceaux:
        return texte

    translator, tokenizer = _charger(gpu)
    tokenizer.src_lang = source

    sources = [tokenizer.convert_ids_to_tokens(tokenizer.encode(m)) for m in morceaux]
    resultats = translator.translate_batch(
        sources, target_prefix=[[cible]] * len(sources), beam_size=4
    )

    traduits: list[str] = []
    for res in resultats:
        tokens = list(res.hypotheses[0])
        if tokens and tokens[0] == cible:  # retire le token de langue cible
            tokens = tokens[1:]
        ids = tokenizer.convert_tokens_to_ids(tokens)
        traduits.append(tokenizer.decode(ids, skip_special_tokens=True).strip())

    return _reconstituer(plan, traduits)
