"""Tests purs de tools/bm_lyon.py (aucune dépendance Playwright)."""

from tools.bm_lyon import (
    artist_name_matches,
    cote_equivalente,
    extraire_part_dieu,
    name_similarity,
    parser_notice,
)


# --- matching artiste ---------------------------------------------------------

def test_artiste_exact():
    assert artist_name_matches("Gaëtan Roussel", "Gaetan Roussel")


def test_artiste_inversion_nom_prenom():
    # La virgule survit à la normalisation → pas 1.0 exactement, mais bien
    # au-dessus du seuil artiste (0.85) grâce au fallback tokens triés.
    assert artist_name_matches("Cosma, Vladimir", "Vladimir Cosma")


def test_artiste_subset_bourvil():
    # Régression Musique_Tools : "Bourvil" (catalogue) vs "André Bourvil"
    # (cherché) doit matcher UNIQUEMENT avec allow_subset=True.
    assert not artist_name_matches("Bourvil", "André Bourvil")
    assert artist_name_matches("Bourvil", "André Bourvil", allow_subset=True)


def test_subset_rejette_tokens_courts():
    # "Air" ⊂ "Air Supply" ne doit PAS matcher (tokens < 5 caractères).
    assert not artist_name_matches("Air", "Air Supply", allow_subset=True)


# --- parsing notice -------------------------------------------------------------

def test_parser_notice_ordre_naturel():
    t, a = parser_notice("Trafic [Disque compact] / Gaëtan Roussel")
    assert t == "Trafic"
    assert a == "Gaëtan Roussel"


def test_parser_notice_sans_auteur():
    t, a = parser_notice("Compilation été [Disque compact]")
    assert t == "Compilation été"
    assert a == ""


# --- extraction Part-Dieu -------------------------------------------------------

def test_extraire_part_dieu_simple():
    txt = "Bibliothèque\nPart-Dieu\n786.2 MAL 1 - En rayon\nAutre"
    cotes, statuts = extraire_part_dieu(txt)
    assert cotes == ["786.2 MAL 1"]
    assert statuts == ["En rayon"]


def test_extraire_part_dieu_statut_avec_tiret():
    # Régression Musique_Tools : le statut contient lui-même " - " ; le split
    # doit se faire sur la PREMIÈRE occurrence, sinon la cote est coupée.
    txt = "Part-Dieu\n782.ARC 61 - Prêté - Retour prévu le : 06/08/2026\n"
    cotes, statuts = extraire_part_dieu(txt)
    assert cotes == ["782.ARC 61"]
    assert statuts == ["Prêté - Retour prévu le : 06/08/2026"]


def test_extraire_part_dieu_multiple_exemplaires():
    txt = ("Part-Dieu\n786.1 KNI 3 - En rayon\nbla\n"
           "Part-Dieu\n786.1 KNI 4 - Prêté - Retour prévu le : 01/09/2026\n")
    cotes, statuts = extraire_part_dieu(txt)
    assert cotes == ["786.1 KNI 3", "786.1 KNI 4"]
    assert statuts[1] == "Prêté - Retour prévu le : 01/09/2026"


def test_extraire_part_dieu_sans_statut():
    cotes, statuts = extraire_part_dieu("Part-Dieu\n786.2 MAL\n")
    assert cotes == ["786.2 MAL"]
    assert statuts == ["Voir dispo"]


def test_cote_dans_le_nom_avec_tiret_nu():
    # Splitter sur "-" nu casserait "782.42-AIR" ; " - " (espacé) est requis.
    cotes, _ = extraire_part_dieu("Part-Dieu\n782.42-AIR - En rayon\n")
    assert cotes == ["782.42-AIR"]


# --- comparaison de cotes -------------------------------------------------------

def test_cote_equivalente_espaces_casse():
    assert cote_equivalente("786.2 MAL 1", "786.2  mal 1")
    assert cote_equivalente(" 786.1 KNI 3 ", "786.1 KNI 3")


def test_cote_differente():
    assert not cote_equivalente("786.2 MAL 1", "786.2 MAL 2")
    assert not cote_equivalente("", "")
