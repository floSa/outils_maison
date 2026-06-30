from pathlib import Path

import streamlit as st

from tools.video import creer_gif

st.title("🎞️ Créer un GIF")
st.caption("Convertit un court extrait de vidéo en GIF animé (palette optimisée).")

chemin = st.text_input("Chemin de la vidéo", placeholder="C:/Users/.../clip.mp4")
col1, col2, col3 = st.columns(3)
debut = col1.text_input("Début (HH:MM:SS)", value="00:00:00")
duree = col2.number_input("Durée (s)", min_value=0.5, value=3.0, step=0.5)
largeur = col3.number_input("Largeur (px)", min_value=120, value=480, step=40)
fps = st.slider("Images par seconde", 5, 24, 12)

if not chemin:
    st.stop()

src = Path(chemin)
if not src.is_file():
    st.error(f"Vidéo introuvable : {src}")
    st.stop()

if st.button("Créer le GIF", type="primary"):
    with st.spinner("Création du GIF…"):
        try:
            sortie = creer_gif(src, debut, duree, fps=fps, largeur=int(largeur))
            st.success(f"GIF créé : `{sortie}`")
            st.image(str(sortie))
        except Exception as e:
            st.error(str(e))
