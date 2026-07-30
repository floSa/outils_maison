"""Filigrane texte en mosaïque pour images et PDF (Pillow + PyMuPDF)."""

from __future__ import annotations

import io
from dataclasses import dataclass, replace
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# Essayés dans l'ordre : DejaVu (Linux/WSL) puis Arial (Windows). Si aucune n'est
# trouvée, on retombe sur la police bitmap intégrée à Pillow.
_CANDIDATS_POLICE = ("DejaVuSans-Bold.ttf", "arialbd.ttf", "Arial Bold.ttf", "Arial.ttf")


@dataclass
class OptionsFiligrane:
    """Paramètres d'un filigrane texte répété en mosaïque."""

    texte: str
    taille_police: int = 40
    couleur: tuple[int, int, int] = (128, 128, 128)
    opacite: float = 0.2  # 0 (invisible) à 1 (opaque)
    angle: float = 45.0  # degrés, sens anti-horaire
    espacement: int = 60  # px ajoutés entre chaque répétition de la mosaïque


def _police(taille: int) -> ImageFont.ImageFont:
    for nom in _CANDIDATS_POLICE:
        try:
            return ImageFont.truetype(nom, taille)
        except OSError:
            continue
    return ImageFont.load_default(size=taille)


def _tuile(options: OptionsFiligrane) -> Image.Image:
    """Rend le texte une fois sur un calque transparent, pivoté, prêt à être carrelé."""
    police = _police(options.taille_police)
    gauche, haut, droite, bas = police.getbbox(options.texte)
    largeur, hauteur = droite - gauche, bas - haut
    marge = max(largeur, hauteur, 1) // 4 + 1
    calque = Image.new("RGBA", (largeur + 2 * marge, hauteur + 2 * marge), (0, 0, 0, 0))
    alpha = round(255 * max(0.0, min(1.0, options.opacite)))
    ImageDraw.Draw(calque).text(
        (marge - gauche, marge - haut), options.texte, font=police, fill=(*options.couleur, alpha)
    )
    return calque.rotate(options.angle, expand=True, resample=Image.BICUBIC)


def _calque_mosaique(taille: tuple[int, int], tuile: Image.Image, espacement: int) -> Image.Image:
    """Carrelage d'une tuile transparente sur tout un calque de la taille donnée."""
    calque = Image.new("RGBA", taille, (0, 0, 0, 0))
    pas_x = tuile.width + espacement
    pas_y = tuile.height + espacement
    for y in range(-tuile.height, taille[1] + tuile.height, pas_y):
        for x in range(-tuile.width, taille[0] + tuile.width, pas_x):
            calque.alpha_composite(tuile, (x, y))
    return calque


def filigraner_image(
    source: str | Path, destination: str | Path, options: OptionsFiligrane
) -> Path:
    """Applique un filigrane texte en mosaïque sur une image et l'enregistre."""
    src = Path(source)
    if not src.is_file():
        raise FileNotFoundError(f"Image introuvable : {src}")

    with Image.open(src) as im:
        base = im.convert("RGBA")
        mosaique = _calque_mosaique(base.size, _tuile(options), options.espacement)
        resultat = Image.alpha_composite(base, mosaique)
        if im.mode != "RGBA":
            resultat = resultat.convert("RGB")

        dest = Path(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        resultat.save(dest)
    return dest


def filigraner_pdf(source: str | Path, destination: str | Path, options: OptionsFiligrane) -> Path:
    """Applique un filigrane texte en mosaïque sur toutes les pages d'un PDF.

    Le filigrane est composé en image (même rendu que pour les images) puis incrusté
    sur chaque page : ce n'est donc pas du texte vectoriel dans le PDF produit.
    """
    import fitz  # PyMuPDF

    src = Path(source)
    if not src.is_file():
        raise FileNotFoundError(f"PDF introuvable : {src}")

    zoom = 2.0  # résolution de la mosaïque plus fine que les 72 pt/pouce du PDF
    options_zoom = replace(
        options,
        taille_police=round(options.taille_police * zoom),
        espacement=round(options.espacement * zoom),
    )
    tuile = _tuile(options_zoom)

    doc = fitz.open(str(src))
    for page in doc:
        taille = (round(page.rect.width * zoom), round(page.rect.height * zoom))
        mosaique = _calque_mosaique(taille, tuile, options_zoom.espacement)
        tampon = io.BytesIO()
        mosaique.save(tampon, format="PNG")
        page.insert_image(page.rect, stream=tampon.getvalue(), overlay=True)

    dest = Path(destination)
    dest.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(dest))
    doc.close()
    return dest
