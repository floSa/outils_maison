from pathlib import Path

import pandas as pd
import streamlit as st

from tools.files import NOM_JOURNAL, annuler, appliquer, previsualiser_remplacement
from ui import champ_dossier

st.title("🔁 Renommer en masse (chercher / remplacer)")
st.caption("Remplace un motif dans les noms de fichiers — texte simple ou expression régulière.")

dossier = champ_dossier(
    "Dossier", "files_remplacer_dossier", placeholder="C:/Users/.../fichiers"
)
col1, col2 = st.columns(2)
chercher = col1.text_input("Chercher")
remplacer = col2.text_input("Remplacer par")

col3, col4, col5 = st.columns(3)
regex = col3.checkbox("Expression régulière", value=False)
recursif = col4.checkbox("Sous-dossiers", value=False)
filtre_ext = col5.text_input("Extensions (ex. .jpg,.png)", value="")

if not dossier or not chercher:
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

try:
    renommages = previsualiser_remplacement(
        base, chercher, remplacer, regex=regex, extensions=extensions, recursif=recursif
    )
except Exception as e:
    st.error(f"Motif invalide : {e}")
    st.stop()

st.markdown("#### Aperçu")
if not renommages:
    st.info("Aucun fichier ne correspond.")
else:
    df = pd.DataFrame([{"Avant": r.ancien.name, "Après": r.nouveau.name} for r in renommages])
    st.dataframe(df, use_container_width=True, hide_index=True)
    if st.button(f"Renommer {len(renommages)} fichier(s)", type="primary"):
        journal = appliquer(renommages, base)
        st.success(f"Renommage effectué (journal : `{journal.name}`).")

st.divider()
if (base / NOM_JOURNAL).is_file():
    if st.button("Annuler le dernier renommage"):
        st.success(f"{annuler(base)} fichier(s) restauré(s).")
