from pathlib import Path

import pandas as pd
import streamlit as st

from tools.files import NOM_JOURNAL, annuler, appliquer, previsualiser_renommage_csv
from ui import FILETYPES_CSV, champ_dossier, champ_fichier

st.title("📋 Renommer depuis un CSV")
st.caption("Renomme des fichiers selon une table de correspondances (colonnes ancien → nouveau).")

dossier = champ_dossier(
    "Dossier des fichiers", "files_csv_dossier", placeholder="C:/Users/.../fichiers"
)
csv_path = champ_fichier(
    "Fichier CSV de correspondances",
    "files_csv_mapping",
    filetypes=FILETYPES_CSV,
    placeholder="C:/Users/.../mapping.csv",
)
col1, col2 = st.columns(2)
col_ancien = col1.text_input("Colonne 'ancien nom'", value="ancien")
col_nouveau = col2.text_input("Colonne 'nouveau nom'", value="nouveau")

if not dossier or not csv_path:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()
if not Path(csv_path).is_file():
    st.error(f"CSV introuvable : {csv_path}")
    st.stop()

try:
    renommages = previsualiser_renommage_csv(
        base, csv_path, col_ancien=col_ancien, col_nouveau=col_nouveau
    )
except ValueError as e:
    st.error(str(e))
    st.stop()

st.markdown("#### Aperçu")
if not renommages:
    st.info("Aucune correspondance applicable (vérifie les noms et les colonnes).")
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
