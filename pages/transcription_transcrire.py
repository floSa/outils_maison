from pathlib import Path

import pandas as pd
import streamlit as st

from tools import transcription
from ui import champ_fichier

FILETYPES_MEDIA = [
    ("Audio / Vidéo", "*.mp3 *.wav *.flac *.m4a *.ogg *.opus *.mp4 *.mkv *.mov *.avi *.webm *.m4v"),
    ("Tous les fichiers", "*.*"),
]

st.title("🎙️ Transcrire un audio / une vidéo")
st.caption(
    "Transcription **locale** (Whisper via faster-whisper, sans PyTorch). "
    "Sort le texte et des sous-titres `.srt`."
)

chemin = champ_fichier("Fichier audio ou vidéo", "transcription_fichier", filetypes=FILETYPES_MEDIA)

# --- Options : modèle, langue, matériel, VAD ------------------------------- #
col1, col2 = st.columns(2)
libelle_modele = col1.selectbox("Modèle", list(transcription.MODELES))
libelle_langue = col2.selectbox("Langue", list(transcription.LANGUES))

col3, col4 = st.columns(2)
if transcription.gpu_disponible():
    materiel = col3.radio("Matériel", ["CPU", "GPU"], horizontal=True)
else:
    materiel = "CPU"
vad = col4.checkbox("Filtrer les silences (VAD)", value=True)

st.caption(
    "Le modèle choisi est téléchargé **au premier usage** (jusqu'à ~1,6 Go pour le turbo), "
    "puis mis en cache hors du projet."
)

if not chemin:
    st.stop()
p = Path(chemin)
if not p.is_file():
    st.error(f"Fichier introuvable : {p}")
    st.stop()

# --- Transcription --------------------------------------------------------- #
if st.button("🎙️ Transcrire", type="primary"):
    barre = st.progress(0.0, "Chargement du modèle (téléchargement au 1er usage)…")
    try:
        resultat = transcription.transcrire(
            p,
            modele=transcription.MODELES[libelle_modele],
            langue=transcription.LANGUES[libelle_langue],
            gpu=(materiel == "GPU"),
            vad=vad,
            progression=lambda f: barre.progress(f, "Transcription en cours…"),
        )
    except Exception as e:  # noqa: BLE001 — message affiché à l'utilisateur
        st.error(f"Échec de la transcription : {e}")
        st.stop()
    barre.empty()

    st.success(
        f"Langue détectée : **{resultat['langue']}** · durée : **{resultat['duree']:.0f} s** · "
        f"{len(resultat['segments'])} segment(s)."
    )
    st.text_area("Texte", value=resultat["texte"], height=220)

    with st.expander("Segments horodatés"):
        st.dataframe(
            pd.DataFrame(resultat["segments"]).rename(
                columns={"debut": "Début (s)", "fin": "Fin (s)", "texte": "Texte"}
            ),
            use_container_width=True,
        )

    nom = p.stem
    col_txt, col_srt, col_vtt = st.columns(3)
    col_txt.download_button(
        "⬇️ Texte (.txt)", resultat["texte"], file_name=f"{nom}.txt", mime="text/plain"
    )
    col_srt.download_button(
        "⬇️ Sous-titres (.srt)",
        transcription.generer_srt(resultat["segments"]),
        file_name=f"{nom}.srt",
        mime="text/plain",
    )
    col_vtt.download_button(
        "⬇️ Sous-titres (.vtt)",
        transcription.generer_vtt(resultat["segments"]),
        file_name=f"{nom}.vtt",
        mime="text/vtt",
    )
