"""Tests de la logique de synthèse vocale (sans télécharger ni charger le modèle)."""

import wave
from pathlib import Path

import numpy as np
import pytest

from tools import tts


def test_voix_contient_le_francais():
    assert "ff_siwis" in {ident for ident, _ in tts.VOIX.values()}
    # La 1re voix proposée est le français.
    premier_ident, premiere_lang = next(iter(tts.VOIX.values()))
    assert premier_ident == "ff_siwis"
    assert premiere_lang == "fr-fr"


def test_dossier_modele_respecte_la_variable_denvironnement(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTILS_TTS_DIR", str(tmp_path / "cache"))
    onnx, voix = tts.chemins_modele()
    assert onnx.parent == tmp_path / "cache"
    assert onnx.name.endswith(".onnx") and voix.name.endswith(".bin")


def test_modele_present_faux_quand_dossier_vide(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTILS_TTS_DIR", str(tmp_path))
    assert tts.modele_present() is False


def test_decouper_texte_vide():
    assert tts.decouper_texte("   \n  ") == []


def test_decouper_texte_court_reste_entier():
    assert tts.decouper_texte("Bonjour le monde.") == ["Bonjour le monde."]


def test_decouper_texte_respecte_la_limite():
    phrases = " ".join(f"Phrase numéro {i} ici." for i in range(200))
    morceaux = tts.decouper_texte(phrases, max_car=100)
    assert len(morceaux) > 1
    assert all(len(m) <= 100 for m in morceaux)


def test_decouper_texte_coupe_une_phrase_geante():
    geante = "a" * 250
    morceaux = tts.decouper_texte(geante, max_car=100)
    assert all(len(m) <= 100 for m in morceaux)
    assert "".join(morceaux) == geante


def test_encoder_wav_valide(tmp_path):
    samples = np.sin(np.linspace(0, 3.14, tts.FREQUENCE_HZ)).astype("float32")
    octets = tts._encoder_wav(samples)
    fichier = tmp_path / "test.wav"
    fichier.write_bytes(octets)
    with wave.open(str(fichier), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getframerate() == tts.FREQUENCE_HZ
        assert w.getnframes() == len(samples)


def test_synthetiser_sans_modele_leve(tmp_path, monkeypatch):
    monkeypatch.setenv("OUTILS_TTS_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        tts.synthetiser("Bonjour", voix="ff_siwis", lang="fr-fr")
