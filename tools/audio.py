"""Outils audio : normalisation FLAC, extraction depuis vidéo, renommage par tags."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from tools.ffmpeg_utils import lancer_ffmpeg
from tools.files import Renommage, nettoyer_nom

# --- A1 : normalisation FLAC -------------------------------------------------

EXT_VIDEO = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v")


@dataclass
class InfoFlac:
    chemin: Path
    sample_rate: int
    bits: int


def info_flac(path: str | Path) -> InfoFlac:
    """Lit fréquence d'échantillonnage et profondeur de bits d'un FLAC (via mutagen)."""
    from mutagen.flac import FLAC

    audio = FLAC(str(path))
    return InfoFlac(
        chemin=Path(path),
        sample_rate=audio.info.sample_rate,
        bits=audio.info.bits_per_sample,
    )


def besoin_normalisation(info: InfoFlac, sr_max: int = 44100, bits_max: int = 16) -> bool:
    return info.sample_rate > sr_max or info.bits > bits_max


def normaliser_flac(
    path: str | Path, *, sr_cible: int = 44100, bits_cible: int = 16
) -> None:
    """Ré-encode un FLAC en 16 bit/44.1 kHz **sur place**, métadonnées préservées."""
    src = Path(path)
    fmt = {16: "s16", 24: "s32"}.get(bits_cible, "s16")
    with tempfile.TemporaryDirectory() as tmp:
        sortie = Path(tmp) / src.name
        lancer_ffmpeg(
            [
                "-i", str(src),
                "-sample_fmt", fmt,
                "-ar", str(sr_cible),
                "-map_metadata", "0",
                "-c:a", "flac",
                str(sortie),
            ]
        )
        sortie.replace(src)  # remplace l'original


def normaliser_dossier(
    dossier: str | Path,
    *,
    recursif: bool = True,
    sr_max: int = 44100,
    bits_max: int = 16,
    log: Callable[[str], None] | None = None,
) -> list[Path]:
    """Normalise tous les FLAC haute résolution d'un dossier. Retourne les fichiers traités."""
    base = Path(dossier)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")

    fichiers = base.rglob("*.flac") if recursif else base.glob("*.flac")
    traites: list[Path] = []
    for f in sorted(fichiers):
        info = info_flac(f)
        if besoin_normalisation(info, sr_max, bits_max):
            if log:
                log(f"Normalisation : {f.name} ({info.sample_rate} Hz / {info.bits} bit)")
            normaliser_flac(f, sr_cible=sr_max, bits_cible=bits_max)
            traites.append(f)
    return traites


# --- A2 : extraction de l'audio d'une vidéo ----------------------------------

CODECS_AUDIO = {
    "flac": ["-c:a", "flac"],
    "mp3": ["-c:a", "libmp3lame", "-q:a", "2"],
    "wav": ["-c:a", "pcm_s16le"],
    "m4a": ["-c:a", "aac", "-b:a", "256k"],
}


def extraire_audio(
    video_path: str | Path, format_sortie: str = "flac", dossier_sortie: str | Path | None = None
) -> Path:
    """Extrait la piste audio d'une vidéo vers un fichier audio (sans ré-encoder la vidéo)."""
    src = Path(video_path)
    if not src.is_file():
        raise FileNotFoundError(f"Vidéo introuvable : {src}")
    if format_sortie not in CODECS_AUDIO:
        raise ValueError(f"Format non géré : {format_sortie} (choix : {', '.join(CODECS_AUDIO)})")

    dossier = Path(dossier_sortie) if dossier_sortie else src.parent
    dossier.mkdir(parents=True, exist_ok=True)
    sortie = dossier / f"{src.stem}.{format_sortie}"

    lancer_ffmpeg(["-i", str(src), "-vn", *CODECS_AUDIO[format_sortie], str(sortie)])
    return sortie


# --- A3 : renommage depuis les tags ------------------------------------------

EXT_AUDIO = (".mp3", ".flac", ".m4a", ".ogg", ".opus", ".wav")


def _tags(path: Path) -> dict[str, str]:
    """Lit quelques tags usuels (artiste, titre, album, piste, année) via mutagen."""
    from mutagen import File as MutaFile

    audio = MutaFile(str(path), easy=True)
    if audio is None:
        return {}

    def prem(cle: str) -> str:
        v = audio.get(cle)
        return str(v[0]) if v else ""

    piste = prem("tracknumber").split("/")[0]
    annee = prem("date")[:4]
    return {
        "artiste": prem("artist"),
        "titre": prem("title"),
        "album": prem("album"),
        "piste": piste,
        "annee": annee,
    }


def nom_depuis_tags(tags: dict[str, str], motif: str) -> str:
    """Construit un nom de fichier depuis un motif, ex. ``{piste} - {artiste} - {titre}``.

    La piste est complétée sur 2 chiffres ; les champs manquants deviennent vides.
    """
    champs = dict(tags)
    piste = champs.get("piste", "")
    champs["piste"] = f"{int(piste):02d}" if piste.isdigit() else piste
    from collections import defaultdict

    nom = motif.format_map(defaultdict(str, champs))
    return nettoyer_nom(nom, minuscule=False, espaces_en=" ").strip()


def previsualiser_renommage_tags(
    dossier: str | Path,
    motif: str = "{piste} - {artiste} - {titre}",
    *,
    recursif: bool = False,
) -> list[Renommage]:
    """Calcule les renommages basés sur les tags, sans rien modifier."""
    base = Path(dossier)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")

    fichiers = base.rglob("*") if recursif else base.iterdir()
    renommages: list[Renommage] = []
    for f in sorted(fichiers):
        if not f.is_file() or f.suffix.lower() not in EXT_AUDIO:
            continue
        tags = _tags(f)
        base_nom = nom_depuis_tags(tags, motif)
        if not base_nom:
            continue
        cible = f.with_name(base_nom + f.suffix.lower())
        if cible != f:
            renommages.append(Renommage(ancien=f, nouveau=cible))
    return renommages
