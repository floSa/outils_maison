"""Outils vidéo : fusion de plusieurs clips en un seul fichier."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from tools.ffmpeg_utils import lancer_ffmpeg


def lister_videos(
    dossier: str | Path, motif: str = "*.mp4"
) -> list[Path]:
    """Liste triée (ordre alphabétique) des vidéos d'un dossier."""
    base = Path(dossier)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")
    return sorted(base.glob(motif))


def fusionner_videos(
    dossier: str | Path,
    nom_sortie: str = "compile.mp4",
    *,
    motif: str = "*.mp4",
    codec: str = "libx264",
    codec_audio: str = "aac",
    log: Callable[[str], None] | None = None,
) -> Path:
    """Fusionne (concatène) toutes les vidéos d'un dossier dans l'ordre alphabétique.

    moviepy est importé paresseusement (lourd) pour ne pas ralentir le reste de l'app.

    :param log: callback optionnel pour les messages de progression.
    :raises FileNotFoundError: si aucune vidéo ne correspond au motif.
    :return: chemin du fichier fusionné.
    """
    from moviepy import VideoFileClip, concatenate_videoclips

    def _log(msg: str) -> None:
        if log:
            log(msg)

    fichiers = lister_videos(dossier, motif)
    if not fichiers:
        raise FileNotFoundError(
            f"Aucune vidéo « {motif} » trouvée dans {dossier}"
        )

    _log(f"{len(fichiers)} vidéo(s) trouvée(s).")
    clips = []
    try:
        for f in fichiers:
            _log(f"Chargement : {f.name}")
            clips.append(VideoFileClip(str(f)))

        _log("Fusion en cours…")
        finale = concatenate_videoclips(clips, method="compose")

        sortie = Path(dossier) / nom_sortie
        _log(f"Export vers : {sortie}")
        finale.write_videofile(
            str(sortie), codec=codec, audio_codec=codec_audio
        )
        finale.close()
        return sortie
    finally:
        for c in clips:
            c.close()


# --- V2 : découper / extraire un passage -------------------------------------

def decouper(
    video_path: str | Path,
    debut: str,
    fin: str,
    sortie: str | Path | None = None,
) -> Path:
    """Extrait le passage [debut, fin] d'une vidéo, **sans ré-encoder** (copie des flux).

    :param debut, fin: horodatages ``HH:MM:SS`` (ou secondes).
    :param sortie: chemin de sortie (défaut : ``<nom>_extrait.<ext>`` à côté du source).
    """
    src = Path(video_path)
    if not src.is_file():
        raise FileNotFoundError(f"Vidéo introuvable : {src}")
    cible = Path(sortie) if sortie else src.with_name(f"{src.stem}_extrait{src.suffix}")

    lancer_ffmpeg(
        ["-ss", str(debut), "-to", str(fin), "-i", str(src), "-c", "copy", str(cible)]
    )
    return cible


# --- V3 : compresser ---------------------------------------------------------

def compresser(
    video_path: str | Path,
    *,
    crf: int = 23,
    hauteur: int | None = None,
    preset: str = "medium",
    sortie: str | Path | None = None,
) -> Path:
    """Ré-encode une vidéo en H.264 pour réduire son poids.

    :param crf: qualité (18 = quasi sans perte, 28 = très compressé). 23 par défaut.
    :param hauteur: redimensionne à cette hauteur (largeur auto, ratio conservé).
    """
    src = Path(video_path)
    if not src.is_file():
        raise FileNotFoundError(f"Vidéo introuvable : {src}")
    cible = Path(sortie) if sortie else src.with_name(f"{src.stem}_compresse.mp4")

    args = ["-i", str(src), "-c:v", "libx264", "-crf", str(crf), "-preset", preset]
    if hauteur:
        args += ["-vf", f"scale=-2:{hauteur}"]
    args += ["-c:a", "aac", "-b:a", "160k", str(cible)]
    lancer_ffmpeg(args)
    return cible
