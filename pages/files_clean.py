from pathlib import Path

import pandas as pd
import streamlit as st

from tools.files import NOM_JOURNAL, annuler, appliquer, previsualiser

st.title("🧹 Nettoyer les noms de fichiers")
st.caption(
    "Normalise les noms : retire accents et caractères spéciaux, remplace les espaces, "
    "met en minuscules. Réversible via un journal d'annulation."
)

dossier = st.text_input("Dossier à traiter", placeholder="C:/Users/.../images")

col1, col2 = st.columns(2)
with col1:
    filtre_ext = st.text_input(
        "Extensions (séparées par des virgules, vide = toutes)",
        placeholder=".jpg, .png, .pdf",
    )
    recursif = st.checkbox("Inclure les sous-dossiers", value=False)
with col2:
    minuscule = st.checkbox("Tout en minuscules", value=True)

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

extensions = tuple(
    e.strip() if e.strip().startswith(".") else f".{e.strip()}"
    for e in filtre_ext.split(",")
    if e.strip()
) or None

renommages = previsualiser(
    base, extensions=extensions, recursif=recursif, minuscule=minuscule
)

st.markdown("#### Aperçu")
if not renommages:
    st.info("Aucun fichier à renommer (tout est déjà propre, ou filtre trop restrictif).")
else:
    df = pd.DataFrame(
        [{"Avant": r.ancien.name, "Après": r.nouveau.name} for r in renommages]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)

    if st.button(f"Renommer {len(renommages)} fichier(s)", type="primary"):
        journal = appliquer(renommages, base)
        st.success(f"Renommage effectué. Journal d'annulation : `{journal}`")

st.divider()
st.markdown("#### Annulation")
if (base / NOM_JOURNAL).is_file():
    st.caption("Un journal d'annulation existe dans ce dossier.")
    if st.button("Annuler le dernier renommage"):
        n = annuler(base)
        st.success(f"{n} fichier(s) restauré(s).")
else:
    st.caption("Aucun journal d'annulation dans ce dossier.")
