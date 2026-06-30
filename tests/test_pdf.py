import pytest
from pypdf import PdfWriter

from tools.pdf import Segment, compter_pages, extraire_segments


def _pdf_factice(chemin, n_pages):
    writer = PdfWriter()
    for _ in range(n_pages):
        writer.add_blank_page(width=200, height=200)
    with open(chemin, "wb") as f:
        writer.write(f)


def test_compter_pages(tmp_path):
    src = tmp_path / "src.pdf"
    _pdf_factice(src, 5)
    assert compter_pages(src) == 5


def test_extraire_segments_ok(tmp_path):
    src = tmp_path / "src.pdf"
    _pdf_factice(src, 10)

    res = extraire_segments(
        src,
        [Segment("chap1", 1, 3), Segment("chap2", 4, 4)],
    )
    assert len(res.crees) == 2
    assert not res.avertissements
    assert compter_pages(res.crees[0]) == 3
    assert compter_pages(res.crees[1]) == 1


def test_extraire_segments_plage_invalide(tmp_path):
    src = tmp_path / "src.pdf"
    _pdf_factice(src, 3)

    res = extraire_segments(src, [Segment("trop_loin", 1, 99)])
    assert not res.crees
    assert len(res.avertissements) == 1


def test_extraire_source_absente(tmp_path):
    with pytest.raises(FileNotFoundError):
        extraire_segments(tmp_path / "nope.pdf", [Segment("x", 1, 1)])


def test_fusionner(tmp_path):
    from tools.pdf import fusionner

    a, b = tmp_path / "a.pdf", tmp_path / "b.pdf"
    _pdf_factice(a, 2)
    _pdf_factice(b, 3)
    res = fusionner([a, b], tmp_path / "fus.pdf")
    assert compter_pages(res) == 5


def test_supprimer_pages(tmp_path):
    from tools.pdf import supprimer_pages

    src = tmp_path / "src.pdf"
    _pdf_factice(src, 5)
    res = supprimer_pages(src, {2, 4}, tmp_path / "out.pdf")
    assert compter_pages(res) == 3


def test_pivoter_angle_invalide(tmp_path):
    from tools.pdf import pivoter_pages

    src = tmp_path / "src.pdf"
    _pdf_factice(src, 1)
    with pytest.raises(ValueError):
        pivoter_pages(src, 45, tmp_path / "out.pdf")


def test_images_pdf_aller_retour(tmp_path):
    from PIL import Image

    from tools.pdf import images_vers_pdf, pdf_vers_images

    img = tmp_path / "p.png"
    Image.new("RGB", (120, 80), (200, 100, 50)).save(img)
    doc = images_vers_pdf([img, img], tmp_path / "doc.pdf")
    assert compter_pages(doc) == 2

    sorties = pdf_vers_images(doc, tmp_path / "rendu", dpi=72)
    assert len(sorties) == 2 and all(p.is_file() for p in sorties)
