from pathlib import Path

import pandas as pd
import streamlit as st

from tools.images import (
    appliquer_renumerotation,
    lister_images,
    previsualiser_renumerotation,
)

st.title("🔢 Renuméroter des images")
st.caption("Renomme des pages/images en séquence selon un tri naturel (page2 avant page10).")

dossier = st.text_input("Dossier des images", placeholder="C:/Users/.../scans")

col1, col2, col3 = st.columns(3)
prefixe = col1.text_input("Préfixe", value="page")
depart = col2.number_input("Numéro de départ", value=1, step=1)
largeur = col3.number_input("Chiffres (zéros à gauche)", value=3, min_value=1, step=1)

col4, col5 = st.columns(2)
inverse = col4.checkbox("Ordre inversé", value=False)
copier = col5.checkbox("Copier (préserver les originaux)", value=True)
sortie = st.text_input("Dossier de sortie (vide = même dossier)", value="")

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

if not lister_images(base):
    st.warning("Aucune image dans ce dossier.")
    st.stop()

plan = previsualiser_renumerotation(
    base,
    prefixe=prefixe,
    depart=int(depart),
    inverse=inverse,
    largeur=int(largeur),
    dossier_sortie=sortie or None,
)

st.markdown("#### Aperçu")
df = pd.DataFrame([{"Avant": r.ancien.name, "Après": r.nouveau.name} for r in plan])
st.dataframe(df, use_container_width=True, hide_index=True)

if st.button(f"Renuméroter {len(plan)} image(s)", type="primary"):
    if not copier and not (sortie or "").strip():
        st.info("Renommage sur place (les originaux seront renommés).")
    res = appliquer_renumerotation(plan, copier=copier)
    st.success(f"{len(res)} image(s) écrite(s).")
