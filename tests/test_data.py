import json

import pandas as pd
import pytest

from tools import data


def test_csv_vers_xlsx_vers_json(tmp_path):
    csv = tmp_path / "t.csv"
    pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}).to_csv(csv, index=False)

    xlsx = data.convertir_tableau(csv, "xlsx")
    assert xlsx.suffix == ".xlsx" and xlsx.is_file()

    js = data.convertir_tableau(xlsx, "json")
    contenu = json.loads(js.read_text(encoding="utf-8"))
    assert contenu == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]


def test_format_sortie_invalide(tmp_path):
    csv = tmp_path / "t.csv"
    pd.DataFrame({"a": [1]}).to_csv(csv, index=False)
    with pytest.raises(ValueError):
        data.convertir_tableau(csv, "parquet")


def test_source_absente(tmp_path):
    with pytest.raises(FileNotFoundError):
        data.convertir_tableau(tmp_path / "nope.csv", "json")


def test_traiter_lignes_dedup():
    lignes, retirees = data.traiter_lignes("b\na\nb\n\na", dedupliquer=True)
    assert lignes == ["b", "a"]
    assert retirees == 3


def test_traiter_lignes_trier_casse():
    lignes, _ = data.traiter_lignes("Banane\nabricot\nCerise", trier=True, ignorer_casse=True)
    assert lignes == ["abricot", "Banane", "Cerise"]


def test_traiter_lignes_garde_ordre_sans_tri():
    lignes, _ = data.traiter_lignes("z\na\nm", dedupliquer=False, trier=False)
    assert lignes == ["z", "a", "m"]
