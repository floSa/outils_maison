"""Outils PDF : extraction de plages de pages vers de nouveaux fichiers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader, PdfWriter


@dataclass
class Segment:
    """Une plage de pages à extraire (numéros 1-indexés, inclusifs)."""

    nom: str
    debut: int
    fin: int


@dataclass
class ResultatExtraction:
    crees: list[Path]
    avertissements: list[str]


def compter_pages(pdf_path: str | Path) -> int:
    """Nombre de pages du PDF source."""
    return len(PdfReader(str(pdf_path)).pages)


def extraire_segments(
    pdf_path: str | Path,
    segments: list[Segment],
    dossier_sortie: str | Path | None = None,
) -> ResultatExtraction:
    """Extrait des plages de pages d'un PDF et écrit un fichier par plage.

    :param pdf_path: chemin du PDF source.
    :param segments: liste de :class:`Segment` (pages 1-indexées, fin incluse).
    :param dossier_sortie: dossier de destination (défaut : dossier du source).
    :raises FileNotFoundError: si le PDF source est introuvable.
    :return: chemins créés et avertissements (plages invalides ignorées).
    """
    source = Path(pdf_path)
    if not source.is_file():
        raise FileNotFoundError(f"PDF source introuvable : {source}")

    sortie = Path(dossier_sortie) if dossier_sortie else source.parent
    sortie.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(str(source))
    max_pages = len(reader.pages)

    crees: list[Path] = []
    avertissements: list[str] = []

    for seg in segments:
        if seg.debut < 1 or seg.fin > max_pages or seg.debut > seg.fin:
            avertissements.append(
                f"Plage invalide pour « {seg.nom} » ({seg.debut}-{seg.fin}) ; "
                f"le PDF a {max_pages} pages. Ignoré."
            )
            continue

        writer = PdfWriter()
        for i in range(seg.debut - 1, seg.fin):
            writer.add_page(reader.pages[i])

        nom_fichier = seg.nom if seg.nom.lower().endswith(".pdf") else f"{seg.nom}.pdf"
        chemin = sortie / nom_fichier
        with open(chemin, "wb") as f:
            writer.write(f)
        crees.append(chemin)

    return ResultatExtraction(crees=crees, avertissements=avertissements)


# --- P2 : fusionner plusieurs PDF --------------------------------------------

def fusionner(pdfs: list[str | Path], sortie: str | Path) -> Path:
    """Concatène plusieurs PDF (dans l'ordre fourni) en un seul fichier."""
    writer = PdfWriter()
    for p in pdfs:
        chemin = Path(p)
        if not chemin.is_file():
            raise FileNotFoundError(f"PDF introuvable : {chemin}")
        writer.append(str(chemin))

    cible = Path(sortie)
    cible.parent.mkdir(parents=True, exist_ok=True)
    with open(cible, "wb") as f:
        writer.write(f)
    return cible


# --- P3 : pivoter / supprimer des pages --------------------------------------

def supprimer_pages(
    pdf_path: str | Path, pages: set[int], sortie: str | Path
) -> Path:
    """Écrit une copie du PDF sans les pages indiquées (numéros 1-indexés)."""
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    for i, page in enumerate(reader.pages, start=1):
        if i not in pages:
            writer.add_page(page)
    cible = Path(sortie)
    with open(cible, "wb") as f:
        writer.write(f)
    return cible


def pivoter_pages(
    pdf_path: str | Path,
    angle: int,
    sortie: str | Path,
    pages: set[int] | None = None,
) -> Path:
    """Pivote des pages d'un multiple de 90°. ``pages=None`` → toutes les pages."""
    if angle % 90 != 0:
        raise ValueError("L'angle doit être un multiple de 90.")
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    for i, page in enumerate(reader.pages, start=1):
        if pages is None or i in pages:
            page.rotate(angle)
        writer.add_page(page)
    cible = Path(sortie)
    with open(cible, "wb") as f:
        writer.write(f)
    return cible


# --- P4 : images ↔ PDF -------------------------------------------------------

def images_vers_pdf(images: list[str | Path], sortie: str | Path) -> Path:
    """Assemble une liste d'images en un seul PDF (une image par page)."""
    from PIL import Image

    if not images:
        raise ValueError("Aucune image fournie.")
    pages = [Image.open(p).convert("RGB") for p in images]
    cible = Path(sortie)
    cible.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(cible, save_all=True, append_images=pages[1:])
    for im in pages:
        im.close()
    return cible


def pdf_vers_images(
    pdf_path: str | Path,
    dossier_sortie: str | Path | None = None,
    *,
    dpi: int = 150,
    format_image: str = "png",
) -> list[Path]:
    """Rend chaque page d'un PDF en image (via PyMuPDF, sans dépendance externe)."""
    import fitz  # PyMuPDF

    src = Path(pdf_path)
    if not src.is_file():
        raise FileNotFoundError(f"PDF introuvable : {src}")
    sortie = Path(dossier_sortie) if dossier_sortie else src.parent / src.stem
    sortie.mkdir(parents=True, exist_ok=True)

    crees: list[Path] = []
    doc = fitz.open(str(src))
    zoom = dpi / 72
    matrice = fitz.Matrix(zoom, zoom)
    for i, page in enumerate(doc, start=1):
        pix = page.get_pixmap(matrix=matrice)
        chemin = sortie / f"{src.stem}_{i:03d}.{format_image}"
        pix.save(str(chemin))
        crees.append(chemin)
    doc.close()
    return crees
