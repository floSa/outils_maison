from pathlib import Path

import streamlit as st

from tools.audio import decouper_audio
from tools.ffmpeg_utils import duree_secondes

st.title("✂️ Découper un audio")
st.caption("Extrait un passage d'un fichier audio (sans ré-encodage).")

chemin = st.text_input("Fichier audio", placeholder="C:/Users/.../piste.flac")

if not chemin:
    st.stop()

src = Path(chemin)
if not src.is_file():
    st.error(f"Fichier introuvable : {src}")
    st.stop()

duree = duree_secondes(src)
if duree:
    m, s = divmod(int(duree), 60)
    st.info(f"Durée : {m:02d}:{s:02d}")

col1, col2 = st.columns(2)
debut = col1.text_input("Début (HH:MM:SS)", value="00:00:00")
fin = col2.text_input("Fin (HH:MM:SS)", value="00:00:30")

if st.button("Découper", type="primary"):
    try:
        sortie = decouper_audio(src, debut, fin)
        st.success(f"Extrait créé : `{sortie}`")
    except Exception as e:
        st.error(str(e))
