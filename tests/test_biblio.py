from tools import biblio


def test_parser_cote_simple():
    [e] = biblio.parser_lignes("Cliff Martinez - The Knick - 786.1 KNI 3")
    assert e.artiste == "Cliff Martinez"
    assert e.album == "The Knick"
    assert e.cote == "786.1 KNI 3"


def test_parser_album_avec_tiret():
    [e] = biblio.parser_lignes("Ahmed Malek - Musique originale. 2 - 786.2 MAL")
    assert e.album == "Musique originale. 2"
    assert e.cote == "786.2 MAL"


def test_parser_sans_cote():
    [e] = biblio.parser_lignes("Anne - Sophie Versnaeyen - La belle époque")
    assert e.cote == ""


def test_tri_par_cote_numerique():
    txt = (
        "B - Album - 786.11 DAN\n"
        "A - Album - 786.1 KNI\n"
        "C - Album - 786.2 MAL\n"
        "Z - Album - 786 BO"
    )
    tries = biblio.trier_par_cote(biblio.parser_lignes(txt))
    cotes = [e.cote for e in tries]
    assert cotes == ["786 BO", "786.1 KNI", "786.11 DAN", "786.2 MAL"]


def test_sans_cote_va_en_fin():
    txt = "A - X - 786.1 KNI\nB - Y - pas de cote"
    tries = biblio.trier_par_cote(biblio.parser_lignes(txt))
    assert tries[-1].artiste == "B"


def test_trier_fichier(tmp_path):
    f = tmp_path / "cotes.txt"
    f.write_text("B - X - 786.2 MAL\nA - Y - 786.1 KNI\n", encoding="utf-8")
    biblio.trier_fichier(f)
    assert f.read_text(encoding="utf-8").splitlines()[0].endswith("786.1 KNI")
