from pathlib import Path

import pytest

from tools import html_md

FIXTURES = Path(__file__).parent / "fixtures"


def test_convertir_fichier_unique(tmp_path):
    resultats = html_md.convertir(FIXTURES / "sample_singlefile.html", tmp_path)

    assert len(resultats) == 1
    r = resultats[0]
    assert r.status == "ok"
    assert r.output is not None and r.output.is_file()
    assert r.output.suffix == ".md"
    assert r.output.read_text(encoding="utf-8").strip()


def test_convertir_dossier_recursif(tmp_path):
    # Deux .html rangés dans des sous-dossiers différents.
    entree = tmp_path / "in"
    (entree / "a").mkdir(parents=True)
    (entree / "b").mkdir()
    (entree / "a" / "page.html").write_bytes((FIXTURES / "sample_singlefile.html").read_bytes())
    (entree / "b" / "math.html").write_bytes((FIXTURES / "sample_math.html").read_bytes())

    sortie = tmp_path / "out"
    resultats = html_md.convertir(entree, sortie)

    assert len(resultats) == 2
    # L'arborescence d'entrée est reproduite sous le dossier de sortie.
    assert all(r.output is not None for r in resultats)
    sous_dossiers = {r.output.parent.name for r in resultats}
    assert sous_dossiers == {"a", "b"}


def test_math_converti_en_latex(tmp_path):
    resultats = html_md.convertir(FIXTURES / "sample_math.html", tmp_path)
    md = resultats[0].output.read_text(encoding="utf-8")
    assert "$" in md  # les formules sont restituées en LaTeX délimité par des $


def test_lister_sources_dossier(tmp_path):
    (tmp_path / "x.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "y.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "z.txt").write_text("pas du html", encoding="utf-8")
    sources = html_md.lister_sources(tmp_path)
    assert [p.name for p in sources] == ["x.html", "y.html"]


def test_entree_absente(tmp_path):
    with pytest.raises(FileNotFoundError):
        html_md.convertir(tmp_path / "nope.html", tmp_path / "out")
