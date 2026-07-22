from pathlib import Path

import streamlit as st

from tools import tts
from ui import FILETYPES_TEXTE, champ_fichier

st.title("🗣️ Lire du texte à voix haute")
st.caption(
    "Synthèse vocale **locale** (Kokoro, open-source, sans PyTorch). "
    "Choisis une voix et la vitesse, puis écoute ou télécharge le résultat."
)

# --- Texte à lire : saisie directe ou fichier .txt ------------------------- #
source = st.radio("Source du texte", ["Saisir", "Fichier .txt"], horizontal=True)
if source == "Saisir":
    texte = st.text_area(
        "Texte à lire", height=220, placeholder="Colle ou écris ton texte ici…"
    )
else:
    chemin = champ_fichier("Fichier texte", "tts_fichier", filetypes=FILETYPES_TEXTE)
    texte = ""
    if chemin:
        p = Path(chemin)
        if p.is_file():
            texte = p.read_text(encoding="utf-8", errors="replace")
            st.caption(f"{len(texte)} caractères chargés.")
        else:
            st.error(f"Fichier introuvable : {p}")

# --- Options : voix, vitesse, matériel ------------------------------------- #
col1, col2 = st.columns(2)
libelle_voix = col1.selectbox("Voix", list(tts.VOIX))
vitesse = col2.slider("Vitesse", 0.5, 2.0, 1.0, 0.1, help="1.0 = vitesse normale")

if tts.gpu_disponible():
    materiel = st.radio("Matériel", ["CPU", "GPU"], horizontal=True)
else:
    materiel = "CPU"

# --- Modèle : téléchargement au premier usage ------------------------------ #
if not tts.modele_present():
    st.warning(
        "Le modèle de synthèse (~340 Mo) n'est pas encore téléchargé. "
        "C'est un téléchargement unique, mis en cache hors du projet."
    )
    if st.button("⬇️ Télécharger le modèle", type="primary"):
        barre = st.progress(0.0, "Téléchargement…")
        tts.telecharger_modele(
            lambda fraction, libelle: barre.progress(fraction, f"Téléchargement — {libelle}")
        )
        st.rerun()
    st.stop()

# --- Synthèse -------------------------------------------------------------- #
if st.button("🔊 Lire", type="primary", disabled=not texte.strip()):
    voix_id, lang = tts.VOIX[libelle_voix]
    with st.spinner("Synthèse en cours…"):
        try:
            wav = tts.synthetiser(
                texte,
                voix=voix_id,
                lang=lang,
                vitesse=vitesse,
                gpu=(materiel == "GPU"),
            )
        except Exception as e:  # noqa: BLE001 — message affiché à l'utilisateur
            st.error(f"Échec de la synthèse : {e}")
            st.stop()
    st.audio(wav, format="audio/wav")
    st.download_button(
        "⬇️ Télécharger le WAV", wav, file_name="lecture.wav", mime="audio/wav"
    )
