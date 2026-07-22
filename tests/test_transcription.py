"""Tests de la logique de transcription (sans télécharger ni charger de modèle)."""

import pytest

from tools import transcription


def test_modeles_contient_le_turbo_par_defaut():
    assert "large-v3-turbo" in transcription.MODELES.values()
    # Le turbo est proposé en premier (défaut).
    assert list(transcription.MODELES.values())[0] == "large-v3-turbo"


def test_langues_detection_auto_et_francais():
    assert transcription.LANGUES["Détection automatique"] is None
    assert transcription.LANGUES["Français"] == "fr"


def test_dossier_modele_respecte_la_variable_denvironnement(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTILS_TRANSCRIPTION_DIR", str(tmp_path / "w"))
    assert transcription.dossier_modele() == tmp_path / "w"


def test_horodatage_srt_et_vtt():
    assert transcription._horodatage(0) == "00:00:00,000"
    assert transcription._horodatage(3661.5) == "01:01:01,500"
    assert transcription._horodatage(3661.5, vtt=True) == "01:01:01.500"


def test_generer_srt():
    segments = [
        {"debut": 0.0, "fin": 1.5, "texte": "Bonjour"},
        {"debut": 1.5, "fin": 3.0, "texte": "le monde"},
    ]
    srt = transcription.generer_srt(segments)
    assert "1\n00:00:00,000 --> 00:00:01,500\nBonjour" in srt
    assert "2\n00:00:01,500 --> 00:00:03,000\nle monde" in srt


def test_generer_vtt():
    segments = [{"debut": 0.0, "fin": 1.5, "texte": "Bonjour"}]
    vtt = transcription.generer_vtt(segments)
    assert vtt.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:01.500" in vtt


def test_transcrire_fichier_absent_leve(tmp_path):
    with pytest.raises(FileNotFoundError):
        transcription.transcrire(tmp_path / "absent.mp3")
