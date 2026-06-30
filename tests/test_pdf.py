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


def test_compresser(tmp_path):
    from tools.pdf import compresser

    src = tmp_path / "src.pdf"
    _pdf_factice(src, 3)
    out = compresser(src)
    assert out.is_file()
    assert compter_pages(out) == 3


def test_proteger_deproteger(tmp_path):
    from pypdf import PdfReader

    from tools.pdf import deproteger, proteger

    src = tmp_path / "src.pdf"
    _pdf_factice(src, 2)

    protege = proteger(src, "secret")
    assert PdfReader(str(protege)).is_encrypted

    with pytest.raises(ValueError):
        deproteger(protege, "mauvais")

    clair = deproteger(protege, "secret")
    assert not PdfReader(str(clair)).is_encrypted


def test_extraire_texte(tmp_path):
    import fitz

    from tools.pdf import extraire_texte

    src = tmp_path / "txt.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Bonjour le monde, ceci est un test de texte.")
    doc.save(str(src))
    doc.close()

    sortie, scanne = extraire_texte(src)
    assert "Bonjour le monde" in sortie.read_text(encoding="utf-8")
    assert scanne is False

    vide = tmp_path / "vide.pdf"
    _pdf_factice(vide, 1)
    _, scanne_vide = extraire_texte(vide)
    assert scanne_vide is True
