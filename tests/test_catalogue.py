import pytest

from tools import catalogue


def _dossier(*parties):
    chemin = parties[0].joinpath(*parties[1:])
    chemin.mkdir(parents=True, exist_ok=True)
    return chemin


def _biblio(racine):
    # __autres : 3 niveaux (Artiste / Album).
    _dossier(racine, "__autres", "Chilla", "Karma")
    _dossier(racine, "__autres", "Chilla", "Mun")
    _dossier(racine, "__autres", "Étienne Daho", "Éden")
    # __MUZAK : 2 niveaux (Categorie / Album).
    _dossier(racine, "__MUZAK", "Nom de l'album")
    _dossier(racine, "__MUZAK", "Œuvre")
    # Album multi-disques : une seule ligne, jamais les CD.
    cd = _dossier(racine, "__MUZAK", "Live", "CD 01")
    _dossier(cd.parent, "CD 02")
    # Dossier caché ignoré, fichier à la racine ignoré.
    _dossier(racine, ".corbeille", "x")
    (racine / "index.txt").write_text("x", encoding="utf-8")


def test_autres_donne_artiste_album(tmp_path):
    _biblio(tmp_path)
    cat = catalogue.scanner(tmp_path)
    assert ("Chilla", "Karma") in cat.lignes
    # jamais « __autres » comme colonne A
    assert all(a != "__autres" for a, _ in cat.lignes)


def test_categorie_donne_categorie_album(tmp_path):
    _biblio(tmp_path)
    cat = catalogue.scanner(tmp_path)
    assert ("__MUZAK", "Nom de l'album") in cat.lignes


def test_multi_disques_une_seule_ligne(tmp_path):
    _biblio(tmp_path)
    cat = catalogue.scanner(tmp_path)
    lignes_live = [t for t in cat.lignes if t[1] == "Live"]
    assert lignes_live == [("__MUZAK", "Live")]
    assert all("CD 01" not in b and "CD 02" not in b for _, b in cat.lignes)


def test_dossier_cache_et_fichiers_ignores(tmp_path):
    _biblio(tmp_path)
    cat = catalogue.scanner(tmp_path)
    noms_a = {a for a, _ in cat.lignes}
    assert ".corbeille" not in noms_a
    # __autres et __MUZAK (préfixe _) NE sont PAS ignorés
    assert {"Chilla", "Étienne Daho", "__MUZAK"} <= (noms_a)


def test_tri_insensible_accents_casse(tmp_path):
    racine = tmp_path
    _dossier(racine, "__MUZAK", "zoo")
    _dossier(racine, "__MUZAK", "Éden")
    _dossier(racine, "__MUZAK", "abba")
    cat = catalogue.scanner(racine)
    albums = [b for a, b in cat.lignes if a == "__MUZAK"]
    assert albums == ["abba", "Éden", "zoo"]


def test_stats_et_total(tmp_path):
    _biblio(tmp_path)
    cat = catalogue.scanner(tmp_path)
    stats = {s.nom: s for s in cat.stats}
    assert stats["__autres"].est_dossier_artistes
    assert stats["__autres"].nb_artistes == 2
    assert stats["__autres"].nb_albums == 3
    assert not stats["__MUZAK"].est_dossier_artistes
    assert stats["__MUZAK"].nb_albums == 3  # Nom de l'album, Œuvre, Live
    assert cat.total_albums == len(cat.lignes) == 6


def test_dossier_artistes_insensible_casse(tmp_path):
    # Le dossier réel est « __Autres » (A majuscule), le défaut « __autres ».
    _dossier(tmp_path, "__Autres", "16 Horsepower", "Sackcloth 'n' Ashes")
    _dossier(tmp_path, "__Autres", "-M-", "Mister Mystère")
    cat = catalogue.scanner(tmp_path)
    # Doit être lu en 3 niveaux : (artiste, album), jamais (__Autres, artiste).
    assert ("16 Horsepower", "Sackcloth 'n' Ashes") in cat.lignes
    assert ("-M-", "Mister Mystère") in cat.lignes
    assert all(a != "__Autres" for a, _ in cat.lignes)
    stats = {s.nom: s for s in cat.stats}
    assert stats["__Autres"].est_dossier_artistes
    assert stats["__Autres"].nb_artistes == 2


def test_dossier_artistes_personnalise(tmp_path):
    _dossier(tmp_path, "__perso", "Artiste", "Album")
    cat = catalogue.scanner(tmp_path, dossiers_artistes=("__perso",))
    assert cat.lignes == [("Artiste", "Album")]


def test_racine_indisponible(tmp_path):
    with pytest.raises(catalogue.RacineIndisponible):
        catalogue.scanner(tmp_path / "inexistant")


def test_refus_ecriture_sous_la_racine(tmp_path):
    _biblio(tmp_path)
    cat = catalogue.scanner(tmp_path)
    with pytest.raises(ValueError, match="sous la racine"):
        catalogue.ecrire_excel(cat, tmp_path / "sortie.xlsx", tmp_path)
    with pytest.raises(ValueError, match="sous la racine"):
        catalogue.ecrire_excel(cat, tmp_path / "__MUZAK" / "sortie.xlsx", tmp_path)


def test_excel_ecrit_colonnes_artiste_album(tmp_path):
    import pandas as pd

    _biblio(tmp_path)
    cat = catalogue.scanner(tmp_path)
    cible = tmp_path.parent / "catalogue.xlsx"
    catalogue.ecrire_excel(cat, cible, tmp_path)

    df = pd.read_excel(cible)
    assert list(df.columns) == ["Artiste", "Album"]
    # une ligne par album (pas d'en-tête compté par pandas)
    assert len(df) == cat.total_albums
    couples = set(map(tuple, df.values.tolist()))
    assert ("Chilla", "Karma") in couples
    # accents et caractères spéciaux préservés
    assert ("Étienne Daho", "Éden") in couples
    assert ("__MUZAK", "Œuvre") in couples
