from pathlib import Path

import streamlit as st

from tools.watermark import OptionsFiligrane, filigraner_image
from ui import FILETYPES_IMAGE, champ_fichier

st.title("💧 Filigrane sur une image")
st.caption("Incruste un texte répété en mosaïque sur une image.")

image = champ_fichier(
    "Chemin de l'image",
    "images_filigrane_image",
    filetypes=FILETYPES_IMAGE,
    placeholder="C:/Users/.../photo.jpg",
)

if not image:
    st.stop()

src = Path(image)
if not src.is_file():
    st.error(f"Image introuvable : {src}")
    st.stop()

texte = st.text_input("Texte du filigrane", value="CONFIDENTIEL")

col1, col2, col3 = st.columns(3)
taille_police = col1.slider("Taille du texte", 10, 300, 60)
angle = col2.slider("Angle (°)", -180, 180, 45)
espacement = col3.slider("Espacement entre répétitions (px)", 0, 500, 80)

col4, col5 = st.columns(2)
couleur = col4.color_picker("Couleur", value="#808080")
opacite = col5.slider("Opacité", 0.0, 1.0, 0.2)

if texte and st.button("Appliquer", type="primary"):
    rgb = tuple(int(couleur.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
    options = OptionsFiligrane(
        texte=texte,
        taille_police=taille_police,
        couleur=rgb,
        opacite=opacite,
        angle=angle,
        espacement=espacement,
    )
    try:
        with st.spinner("Application du filigrane…"):
            sortie = filigraner_image(
                src, src.with_name(f"{src.stem}_filigrane{src.suffix}"), options
            )
        st.success(f"Créé : `{sortie}`")
        st.image(str(sortie))
    except Exception as e:
        st.error(str(e))
