from tools.files import (
    annuler,
    appliquer,
    arborescence_vers_df,
    comparer_dossiers,
    nettoyer_nom,
    previsualiser,
    previsualiser_remplacement,
    previsualiser_rangement,
    previsualiser_renommage_csv,
    statistiques,
    trouver_doublons_fichiers,
)


def test_nettoyer_nom_accents_espaces_casse():
    assert nettoyer_nom("Café de la Gare") == "cafe_de_la_gare"


def test_nettoyer_nom_caracteres_speciaux():
    assert nettoyer_nom("Niv-Mizzet (visionnaire)!") == "niv-mizzet_visionnaire"


def test_nettoyer_nom_garde_casse_si_demande():
    assert nettoyer_nom("Mon Fichier", minuscule=False) == "Mon_Fichier"


def test_previsualiser_filtre_extension(tmp_path):
    (tmp_path / "Photo Été.JPG").write_text("x")
    (tmp_path / "doc.txt").write_text("x")

    rens = previsualiser(tmp_path, extensions=(".jpg",))
    assert len(rens) == 1
    assert rens[0].nouveau.name == "photo_ete.jpg"


def test_appliquer_puis_annuler(tmp_path):
    f = tmp_path / "Été 2024.txt"
    f.write_text("x")

    rens = previsualiser(tmp_path)
    appliquer(rens, tmp_path)

    assert (tmp_path / "ete_2024.txt").is_file()
    assert not f.is_file()

    n = annuler(tmp_path)
    assert n == 1
    assert f.is_file()


def test_appliquer_ignore_collision(tmp_path):
    (tmp_path / "Fichier.txt").write_text("a")
    (tmp_path / "fichier.txt").write_text("b")  # cible déjà prise (sur systèmes sensibles à la casse)

    # Ne doit pas planter ni écraser : on vérifie juste l'absence d'exception.
    rens = previsualiser(tmp_path)
    appliquer(rens, tmp_path)


def test_remplacement_texte(tmp_path):
    (tmp_path / "photo_2023.jpg").write_text("x")
    (tmp_path / "photo_2024.jpg").write_text("x")
    rens = previsualiser_remplacement(tmp_path, "photo", "img")
    assert {r.nouveau.name for r in rens} == {"img_2023.jpg", "img_2024.jpg"}


def test_remplacement_regex(tmp_path):
    (tmp_path / "IMG-001.png").write_text("x")
    rens = previsualiser_remplacement(tmp_path, r"IMG-(\d+)", r"photo_\1", regex=True)
    assert rens[0].nouveau.name == "photo_001.png"


def test_doublons_fichiers(tmp_path):
    (tmp_path / "a.txt").write_text("contenu identique")
    (tmp_path / "b.txt").write_text("contenu identique")
    (tmp_path / "c.txt").write_text("autre")
    groupes = trouver_doublons_fichiers(tmp_path)
    assert len(groupes) == 1
    assert {p.name for p in groupes[0]} == {"a.txt", "b.txt"}


def test_arborescence_vers_df(tmp_path):
    (tmp_path / "artiste" / "album").mkdir(parents=True)
    df = arborescence_vers_df([tmp_path])
    assert "Niveau 1" in df.columns
    assert "artiste" in df["Niveau 1"].values


def test_rangement_par_type(tmp_path):
    (tmp_path / "photo.jpg").write_text("x")
    (tmp_path / "musique.mp3").write_text("x")
    (tmp_path / "doc.pdf").write_text("x")
    rens = previsualiser_rangement(tmp_path, mode="type")
    cibles = {r.ancien.name: r.nouveau.parent.name for r in rens}
    assert cibles == {"photo.jpg": "Images", "musique.mp3": "Audio", "doc.pdf": "Documents"}


def test_rangement_puis_appliquer(tmp_path):
    (tmp_path / "a.png").write_text("x")
    rens = previsualiser_rangement(tmp_path, mode="type")
    appliquer(rens, tmp_path)
    assert (tmp_path / "Images" / "a.png").is_file()


def test_statistiques(tmp_path):
    (tmp_path / "a.txt").write_text("12345")
    (tmp_path / "b.jpg").write_text("12")
    (tmp_path / "vide").mkdir()
    stats = statistiques(tmp_path)
    assert stats["nb_fichiers"] == 2
    assert stats["taille_totale"] == 7
    assert stats["plus_gros"][0][0].name == "a.txt"
    assert any(d.name == "vide" for d in stats["dossiers_vides"])


def test_comparer_dossiers(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "commun.txt").write_text("meme")
    (b / "commun.txt").write_text("meme")
    (a / "seul_a.txt").write_text("x")
    (b / "different.txt").write_text("court")
    (a / "different.txt").write_text("beaucoup plus long")
    res = comparer_dossiers(a, b)
    assert res["seulement_a"] == ["different.txt", "seul_a.txt"] or "seul_a.txt" in res["seulement_a"]
    assert "different.txt" in res["differents"]
    assert res["identiques"] == 1


def test_renommage_csv(tmp_path):
    (tmp_path / "vieux.txt").write_text("x")
    csv = tmp_path / "map.csv"
    csv.write_text("ancien,nouveau\nvieux.txt,neuf.txt\n", encoding="utf-8")
    rens = previsualiser_renommage_csv(tmp_path, csv)
    assert len(rens) == 1
    assert rens[0].nouveau.name == "neuf.txt"
