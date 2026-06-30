from pathlib import Path

import numpy as np
from PIL import Image

from tools import images


def _img_bruit(chemin, graine):
    rng = np.random.default_rng(graine)
    arr = rng.integers(0, 256, size=(64, 64, 3), dtype="uint8")
    Image.fromarray(arr).save(chemin)


def test_tri_naturel():
    noms = [Path("p10.png"), Path("p2.png"), Path("p1.png")]
    assert [p.name for p in images.tri_naturel(noms)] == ["p1.png", "p2.png", "p10.png"]


def test_doublons_images(tmp_path):
    _img_bruit(tmp_path / "a.png", 1)
    # copie exacte de a → doublon visuel
    Image.open(tmp_path / "a.png").save(tmp_path / "a_copie.png")
    _img_bruit(tmp_path / "b.png", 999)  # image différente

    groupes = images.trouver_doublons(tmp_path, seuil=2)
    assert len(groupes) == 1
    assert {p.name for p in groupes[0]} == {"a.png", "a_copie.png"}


def test_convertir(tmp_path):
    _img_bruit(tmp_path / "x.png", 3)
    dest = images.convertir(tmp_path / "x.png", "jpg")
    assert dest.suffix == ".jpg" and dest.is_file()


def test_redimensionner_conserve_ratio(tmp_path):
    Image.new("RGB", (400, 200), (10, 20, 30)).save(tmp_path / "g.png")
    dest = images.redimensionner(tmp_path / "g.png", tmp_path / "g_small.jpg", largeur_max=100)
    assert Image.open(dest).size == (100, 50)


def test_renumerotation_copie(tmp_path):
    for n in ["p2.png", "p10.png", "p1.png"]:
        Image.new("RGB", (8, 8), (0, 0, 0)).save(tmp_path / n)
    plan = images.previsualiser_renumerotation(tmp_path, prefixe="img", largeur=2)
    assert [r.nouveau.name for r in plan] == ["img_01.png", "img_02.png", "img_03.png"]
    res = images.appliquer_renumerotation(plan, copier=True)
    assert all(p.is_file() for p in res)
    assert (tmp_path / "p1.png").is_file()  # originaux préservés
