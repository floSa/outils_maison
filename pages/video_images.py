from pathlib import Path

import streamlit as st

from tools.video import extraire_images

st.title("🖼️ Extraire des images d'une vidéo")
st.caption("Capture une image à intervalle régulier (ex. 1 image toutes les N secondes).")

chemin = st.text_input("Chemin de la vidéo", placeholder="C:/Users/.../film.mp4")
col1, col2 = st.columns(2)
intervalle = col1.number_input("Intervalle (secondes)", min_value=0.1, value=1.0, step=0.5)
fmt = col2.selectbox("Format des images", ["png", "jpg"], index=0)

if not chemin:
    st.stop()

src = Path(chemin)
if not src.is_file():
    st.error(f"Vidéo introuvable : {src}")
    st.stop()

if st.button("Extraire", type="primary"):
    with st.spinner("Extraction des images…"):
        try:
            dossier = extraire_images(src, intervalle_s=intervalle, format_image=fmt)
            nb = len(list(dossier.glob(f"*.{fmt}")))
            st.success(f"{nb} image(s) extraite(s) dans `{dossier}`")
        except Exception as e:
            st.error(str(e))
