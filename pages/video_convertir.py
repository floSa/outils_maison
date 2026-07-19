from pathlib import Path

import streamlit as st

from tools.video import convertir
from ui import FILETYPES_VIDEO, champ_fichier

st.title("🔄 Convertir une vidéo")
st.caption("Ré-encode une vidéo vers un autre conteneur (mp4, mkv, webm…) en H.264/AAC.")

chemin = champ_fichier(
    "Chemin de la vidéo",
    "video_convertir_chemin",
    filetypes=FILETYPES_VIDEO,
    placeholder="C:/Users/.../film.mkv",
)
format_sortie = st.selectbox("Format de sortie", ["mp4", "mkv", "webm", "mov"], index=0)

if not chemin:
    st.stop()

src = Path(chemin)
if not src.is_file():
    st.error(f"Vidéo introuvable : {src}")
    st.stop()

if st.button("Convertir", type="primary"):
    with st.spinner("Conversion en cours…"):
        try:
            sortie = convertir(src, format_sortie)
            st.success(f"Créé : `{sortie}`")
        except Exception as e:
            st.error(str(e))
