import importlib.util

import numpy as np
import pytest

cv2_absent = importlib.util.find_spec("cv2") is None
pytestmark = pytest.mark.skipif(cv2_absent, reason="extra vision (opencv) non installé")

if not cv2_absent:
    import cv2

    from tools import fonds


def _paysage(graine, taille=(800, 450)):
    """Texture unique (nuage basse fréquence + quelques blobs), reproductible.

    Une vraie photo donne des features distinctives ; un motif répétitif
    (mêmes cercles partout) tromperait RANSAC, d'où le nuage propre à chaque graine.
    """
    rng = np.random.default_rng(graine)
    w, h = taille
    petit = rng.integers(0, 255, (h // 16, w // 16, 3), dtype=np.uint8)
    img = cv2.resize(petit, (w, h), interpolation=cv2.INTER_CUBIC)
    for _ in range(25):
        centre = (int(rng.integers(0, w)), int(rng.integers(0, h)))
        rayon = int(rng.integers(6, 22))
        couleur = tuple(int(x) for x in rng.integers(0, 255, 3))
        cv2.circle(img, centre, rayon, couleur, -1)
    return img


def _portrait_depuis(paysage):
    """Recadre une bande verticale et l'agrandit en portrait (zoom)."""
    h, w, _ = paysage.shape
    bande_w = w // 3
    x0 = w // 2 - bande_w // 2
    crop = paysage[:, x0 : x0 + bande_w]
    return cv2.resize(crop, (1080, 1920), interpolation=cv2.INTER_CUBIC)


def _ecrire(chemin, img):
    cv2.imwrite(str(chemin), img)


def test_orientation():
    assert fonds.orientation((1920, 1080)) == "paysage"
    assert fonds.orientation((1080, 1920)) == "portrait"
    assert fonds.orientation((500, 500)) == "carre"


def test_inliers_vrai_vs_faux(tmp_path):
    pa = _paysage(1)
    po = _portrait_depuis(pa)
    autre = _paysage(999)  # sans rapport
    _ecrire(tmp_path / "pa.png", pa)
    _ecrire(tmp_path / "po.png", po)
    _ecrire(tmp_path / "autre.png", autre)

    d_pa = fonds.descripteurs(tmp_path / "pa.png")
    d_po = fonds.descripteurs(tmp_path / "po.png")
    d_autre = fonds.descripteurs(tmp_path / "autre.png")

    vrai = fonds.compter_inliers(d_po, d_pa)
    faux = fonds.compter_inliers(d_po, d_autre)
    assert vrai >= 30          # le vrai recadrage est bien reconnu
    assert faux < vrai         # et nettement au-dessus de l'image sans rapport


def test_apparier_synthetique(tmp_path):
    for n in (1, 2):
        pa = _paysage(n)
        _ecrire(tmp_path / f"pa{n}.png", pa)
        _ecrire(tmp_path / f"po{n}.png", _portrait_depuis(pa))

    res = fonds.apparier(tmp_path, seuil=20)
    assert len(res.couples) == 2
    assert not res.paysages_seuls and not res.portraits_seuls
    # chaque portrait apparié au bon paysage (même numéro)
    for c in res.couples:
        assert c.paysage.name[2] == c.portrait.name[2]  # "pa1"/"po1" → caractère index 2


def test_prochain_id_et_ranger(tmp_path):
    source = tmp_path / "src"
    tries = tmp_path / "tries"
    source.mkdir()
    tries.mkdir()
    (tries / "001_pa.png").write_bytes(b"x")
    (tries / "001_po.png").write_bytes(b"x")
    assert fonds.prochain_id(tries) == 2

    pa = source / "p.png"
    po = source / "q.png"
    _ecrire(pa, _paysage(5))
    _ecrire(po, _portrait_depuis(_paysage(5)))
    couple = fonds.Couple(paysage=pa, portrait=po, score=100, second=2)

    faits = fonds.ranger([couple], tries, deplacer=False)
    assert faits[0][0] == "002"
    assert (tries / "002_pa.png").is_file()
    assert (tries / "002_po.png").is_file()
    assert pa.is_file()  # copie : source conservée
