import pytest
from PIL import Image
from pypdf import PdfWriter

from tools.watermark import OptionsFiligrane, filigraner_image, filigraner_pdf


def _pdf_factice(chemin, n_pages=2):
    writer = PdfWriter()
    for _ in range(n_pages):
        writer.add_blank_page(width=200, height=200)
    with open(chemin, "wb") as f:
        writer.write(f)


def test_filigraner_image_meme_taille(tmp_path):
    src = tmp_path / "src.png"
    Image.new("RGB", (300, 200), (255, 255, 255)).save(src)

    dest = filigraner_image(src, tmp_path / "src_filigrane.png", OptionsFiligrane(texte="TEST"))

    assert dest.is_file()
    with Image.open(dest) as im:
        assert im.size == (300, 200)
        # Le filigrane doit avoir modifié au moins un pixel du fond blanc uni.
        assert im.convert("RGB").getextrema() != ((255, 255), (255, 255), (255, 255))


def test_filigraner_image_source_absente(tmp_path):
    with pytest.raises(FileNotFoundError):
        filigraner_image(tmp_path / "nope.png", tmp_path / "sortie.png", OptionsFiligrane(texte="X"))


def test_filigraner_pdf_meme_nombre_de_pages(tmp_path):
    src = tmp_path / "src.pdf"
    _pdf_factice(src, n_pages=3)

    dest = filigraner_pdf(src, tmp_path / "src_filigrane.pdf", OptionsFiligrane(texte="TEST"))

    assert dest.is_file()
    from pypdf import PdfReader

    assert len(PdfReader(str(dest)).pages) == 3


def test_filigraner_pdf_source_absente(tmp_path):
    with pytest.raises(FileNotFoundError):
        filigraner_pdf(tmp_path / "nope.pdf", tmp_path / "sortie.pdf", OptionsFiligrane(texte="X"))
