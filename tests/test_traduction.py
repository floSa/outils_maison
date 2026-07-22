"""Tests de la logique de traduction (sans télécharger ni charger le modèle)."""

from pathlib import Path

import pytest

from tools import traduction


def test_langues_contient_anglais_et_francais():
    assert traduction.LANGUES["Anglais"] == "eng_Latn"
    assert traduction.LANGUES["Français"] == "fra_Latn"
    # L'anglais puis le français sont en tête (cas d'usage principal).
    assert list(traduction.LANGUES)[:2] == ["Anglais", "Français"]


def test_codes_flores_bien_formes():
    # Tous les codes suivent le motif FLORES-200 « xxx_Yyyy ».
    import re

    for code in traduction.LANGUES.values():
        assert re.fullmatch(r"[a-z]{3}_[A-Z][a-z]{3}", code), code


def test_dossier_modele_respecte_la_variable_denvironnement(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTILS_TRADUCTION_DIR", str(tmp_path / "cache"))
    assert traduction.dossier_modele() == tmp_path / "cache"


def test_modele_present_faux_quand_dossier_vide(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTILS_TRADUCTION_DIR", str(tmp_path))
    assert traduction.modele_present() is False


def test_decouper_texte_vide():
    assert traduction.decouper_texte("   \n  ") == []


def test_decouper_texte_court_reste_entier():
    assert traduction.decouper_texte("Hello world.") == ["Hello world."]


def test_decouper_texte_respecte_la_limite():
    phrases = " ".join(f"Sentence number {i} here." for i in range(200))
    morceaux = traduction.decouper_texte(phrases, max_car=80)
    assert len(morceaux) > 1
    assert all(len(m) <= 80 for m in morceaux)


def test_traduire_sans_modele_leve(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTILS_TRADUCTION_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        traduction.traduire("Hello", source="eng_Latn", cible="fra_Latn")
