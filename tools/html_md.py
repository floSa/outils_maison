"""Conversion de captures HTML (SingleFile) en Markdown propre.

Logique pure, réutilisée par la page ``pages/files_html_md.py``. Le moteur
(hygiène → extraction → Markdown, images en ``_assets/``) est le projet
``html_to_md`` copié dans le sous-package :mod:`tools.html_to_md`.

Accepte un fichier ``.html`` unique **ou** un dossier (parcouru récursivement) et
écrit les ``.md`` dans un dossier de sortie, en conservant l'arborescence
d'entrée. Chaque fichier donne un :class:`Result` (ok / review / error) ; un
fichier corrompu n'interrompt pas le lot.
"""

from __future__ import annotations

from pathlib import Path

from tools.html_to_md.convert import MIN_IMAGE_BYTES
from tools.html_to_md.core import Result, process_file
from tools.html_to_md.extract import load_profiles

# Profils d'extraction par site, copiés à côté du moteur vendorisé.
CONFIG_PROFILS = Path(__file__).parent / "html_to_md" / "selectors.yaml"


def lister_sources(entree: Path) -> list[Path]:
    """Fichiers ``.html`` à traiter : le fichier seul, ou tous ceux d'un dossier."""
    if entree.is_file():
        return [entree]
    return sorted(p for p in entree.rglob("*.html") if p.is_file())


def _dossier_sortie(source: Path, entree: Path, sortie: Path) -> Path:
    """Reproduit l'arborescence d'entrée sous le dossier de sortie."""
    if entree.is_dir():
        return sortie / source.relative_to(entree).parent
    return sortie


def convertir(
    entree: Path,
    sortie: Path,
    min_image_bytes: int = MIN_IMAGE_BYTES,
) -> list[Result]:
    """Convertit ``entree`` (fichier ``.html`` ou dossier) vers des ``.md`` dans ``sortie``.

    Renvoie un :class:`Result` par fichier traité, dans l'ordre. Lève
    ``FileNotFoundError`` si ``entree`` n'existe pas.
    """
    entree, sortie = Path(entree), Path(sortie)
    if not entree.exists():
        raise FileNotFoundError(f"Introuvable : {entree}")

    profils = load_profiles(CONFIG_PROFILS)
    sources = lister_sources(entree)

    resultats: list[Result] = []
    taken: set[Path] = set()  # partagé entre fichiers : évite les collisions de noms
    for source in sources:
        out_dir = _dossier_sortie(source, entree, sortie)
        try:
            resultat = process_file(
                source, out_dir, profils,
                min_image_bytes=min_image_bytes, taken=taken,
            )
        except Exception as exc:  # un fichier corrompu ne doit pas stopper le lot
            resultat = Result(
                source=source, output=None, strategy="-", chars_in=0,
                chars_out=0, images=0, status="error", detail=str(exc),
            )
        resultats.append(resultat)
    return resultats
