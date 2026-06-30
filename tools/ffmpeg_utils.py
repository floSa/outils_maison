"""Accès à ffmpeg : on réutilise le binaire embarqué par imageio-ffmpeg.

Évite de dépendre d'un ffmpeg installé sur le système / dans le PATH.
"""

from __future__ import annotations

import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Sequence


@lru_cache(maxsize=1)
def chemin_ffmpeg() -> str:
    """Chemin du binaire ffmpeg (embarqué par imageio-ffmpeg)."""
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def lancer_ffmpeg(
    args: Sequence[str], *, ecraser: bool = True
) -> subprocess.CompletedProcess:
    """Lance ffmpeg avec les arguments donnés (hors binaire et `-y`/`-i`).

    :param args: arguments ffmpeg (entrée/sortie compris).
    :param ecraser: ajoute ``-y`` pour écraser la sortie sans demander.
    :raises RuntimeError: si ffmpeg retourne un code non nul (avec stderr).
    """
    cmd = [chemin_ffmpeg(), "-hide_banner", "-loglevel", "error"]
    if ecraser:
        cmd.append("-y")
    cmd.extend(args)

    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"ffmpeg a échoué :\n{res.stderr.strip()}")
    return res


def duree_secondes(media_path: str | Path) -> float | None:
    """Durée d'un média en secondes via ffmpeg (None si indéterminable)."""
    cmd = [chemin_ffmpeg(), "-hide_banner", "-i", str(media_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    # ffmpeg écrit les infos du média sur stderr, même sans sortie.
    for ligne in res.stderr.splitlines():
        ligne = ligne.strip()
        if ligne.startswith("Duration:"):
            valeur = ligne.split("Duration:")[1].split(",")[0].strip()
            if valeur == "N/A":
                return None
            h, m, s = valeur.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return None
