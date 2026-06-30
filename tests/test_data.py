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
