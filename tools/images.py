"""Outils images : redimensionner, convertir, dédupliquer, renuméroter."""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path

EXT_IMAGES = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic", ".heif")


def _ouvrir_avec_heic():
    """Active le support HEIC/HEIF dans Pillow (photos iPhone)."""
    import pillow_heif

    pillow_heif.register_heif_opener()


def lister_images(dossier: str | Path, *, recursif: bool = False) -> list[Path]:
    base = Path(dossier)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")
    it = base.rglob("*") if recursif else base.iterdir()
    return sorted(f for f in it if f.is_file() and f.suffix.lower() in EXT_IMAGES)


# --- I1 : redimensionner / compresser ----------------------------------------

def redimensionner(
    src: str | Path,
    dest: str | Path,
    *,
    largeur_max: int | None = None,
    hauteur_max: int | None = None,
    qualite: int = 85,
) -> Path:
    """Redimensionne une image (ratio conservé) et la ré-enregistre compressée.

    Si ni largeur ni hauteur ne sont fournies, seule la compression s'applique.
    """
    from PIL import Image

    _ouvrir_avec_heic()
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        if largeur_max or hauteur_max:
            im.thumbnail(
                (largeur_max or im.width, hauteur_max or im.height),
                Image.LANCZOS,
            )
        params = {}
        if dest.suffix.lower() in (".jpg", ".jpeg", ".webp"):
            params = {"quality": qualite, "optimize": True}
            im = im.convert("RGB")
        im.save(dest, **params)
    return dest


# --- I2 : convertir de format ------------------------------------------------

def convertir(src: str | Path, format_sortie: str, *, qualite: int = 90) -> Path:
    """Convertit une image vers un autre format (jpg, png, webp…). Gère le HEIC en entrée."""
    from PIL import Image

    _ouvrir_avec_heic()
    src = Path(src)
    dest = src.with_suffix(f".{format_sortie.lower().lstrip('.')}")
    with Image.open(src) as im:
        params = {}
        if dest.suffix.lower() in (".jpg", ".jpeg", ".webp"):
            params = {"quality": qualite, "optimize": True}
            im = im.convert("RGB")
        im.save(dest, **params)
    return dest


# --- I3 : doublons perceptuels -----------------------------------------------

def empreinte(path: str | Path):
    """Hash perceptuel (pHash) d'une image."""
    import imagehash
    from PIL import Image

    _ouvrir_avec_heic()
    with Image.open(path) as im:
        return imagehash.phash(im)


def trouver_doublons(
    dossier: str | Path, *, recursif: bool = False, seuil: int = 5
) -> list[list[Path]]:
    """Regroupe les images visuellement proches (distance de Hamming ≤ seuil).

    Retourne uniquement les groupes d'au moins 2 images.
    """
    images = lister_images(dossier, recursif=recursif)
    empreintes = []
    for f in images:
        try:
            empreintes.append((f, empreinte(f)))
        except Exception:
            continue  # fichier illisible : ignoré

    groupes: list[list[Path]] = []
    deja: set[int] = set()
    for i, (fi, hi) in enumerate(empreintes):
        if i in deja:
            continue
        groupe = [fi]
        for j in range(i + 1, len(empreintes)):
            if j in deja:
                continue
            fj, hj = empreintes[j]
            if (hi - hj) <= seuil:
                groupe.append(fj)
                deja.add(j)
        if len(groupe) > 1:
            groupes.append(groupe)
    return groupes


# --- I4 : renuméroter en tri naturel (généralisé depuis Dicobat) -------------

def tri_naturel(paths: list[Path]) -> list[Path]:
    """Tri 'naturel' façon Windows : page2 avant page10."""

    def cle(p: Path):
        return [
            int(t) if t.isdigit() else t.lower()
            for t in re.split(r"(\d+)", p.name)
        ]

    return sorted(paths, key=cle)


@dataclass
class Renumerotation:
    ancien: Path
    nouveau: Path


def previsualiser_renumerotation(
    dossier: str | Path,
    *,
    prefixe: str = "page",
    depart: int = 1,
    pas: int = 1,
    inverse: bool = False,
    largeur: int = 3,
    dossier_sortie: str | Path | None = None,
) -> list[Renumerotation]:
    """Calcule la renumérotation des images d'un dossier (tri naturel), sans modifier.

    :param inverse: numérote de la dernière vers la première image.
    :param largeur: nombre de chiffres (zéros à gauche), ex. 3 → ``page_001``.
    """
    images = tri_naturel(lister_images(dossier))
    if inverse:
        images = list(reversed(images))

    sortie = Path(dossier_sortie) if dossier_sortie else Path(dossier)
    plan: list[Renumerotation] = []
    num = depart
    for f in images:
        nouveau_nom = f"{prefixe}_{num:0{largeur}d}{f.suffix.lower()}"
        plan.append(Renumerotation(ancien=f, nouveau=sortie / nouveau_nom))
        num += pas
    return plan


def appliquer_renumerotation(
    plan: list[Renumerotation], *, copier: bool = True
) -> list[Path]:
    """Applique la renumérotation. ``copier=True`` préserve les originaux.

    Passe par des noms temporaires pour éviter d'écraser un fichier de la séquence.
    """
    if not plan:
        return []
    plan[0].nouveau.parent.mkdir(parents=True, exist_ok=True)

    resultats: list[Path] = []
    if copier:
        for r in plan:
            shutil.copy2(r.ancien, r.nouveau)
            resultats.append(r.nouveau)
    else:
        # Déplacement en 2 temps (via .tmp) pour gérer les permutations sur place.
        temporaires = []
        for i, r in enumerate(plan):
            tmp = r.nouveau.with_suffix(r.nouveau.suffix + f".tmp{i}")
            r.ancien.rename(tmp)
            temporaires.append((tmp, r.nouveau))
        for tmp, final in temporaires:
            tmp.rename(final)
            resultats.append(final)
    return resultats
