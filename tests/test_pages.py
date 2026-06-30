"""Smoke-test de rendu : chaque page doit s'exécuter sans exception (entrées vides)."""

import glob

import pytest
from streamlit.testing.v1 import AppTest

PAGES = sorted(glob.glob("pages/*.py"))


@pytest.mark.parametrize("chemin", PAGES, ids=lambda p: p.split("/")[-1])
def test_page_se_rend_sans_exception(chemin):
    at = AppTest.from_file(chemin, default_timeout=30).run()
    assert not at.exception, f"{chemin} a levé : {at.exception}"
