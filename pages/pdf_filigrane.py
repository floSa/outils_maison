from pathlib import Path

import streamlit as st

from tools.watermark import OptionsFiligrane, filigraner_pdf
from ui import FILETYPES_PDF, champ_fichier

st.title("💧 Filigrane sur un PDF")
st.caption("Incruste un texte répété en mosaïque sur toutes les pages d'un PDF.")

pdf = champ_fichier(
    "Chemin du PDF",
    "pdf_filigrane_pdf",
    filetypes=FILETYPES_PDF,
    placeholder="C:/Users/.../document.pdf",
)

if not pdf:
    st.stop()

src = Path(pdf)
if not src.is_file():
    st.error(f"PDF introuvable : {src}")
    st.stop()

texte = st.text_input("Texte du filigrane", value="CONFIDENTIEL")

col1, col2, col3 = st.columns(3)
taille_police = col1.slider("Taille du texte", 10, 150, 40)
angle = col2.slider("Angle (°)", -180, 180, 45)
espacement = col3.slider("Espacement entre répétitions (px)", 0, 300, 60)

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
            sortie = filigraner_pdf(src, src.with_name(f"{src.stem}_filigrane.pdf"), options)
        st.success(f"Créé : `{sortie}`")
    except Exception as e:
        st.error(str(e))
