from pathlib import Path

import streamlit as st

from tools.data import FORMATS, convertir_tableau
from ui import FILETYPES_TABLEAU, champ_fichier

st.title("🔀 Convertir un tableau (CSV ↔ Excel ↔ JSON)")
st.caption("Convertit un fichier tabulaire d'un format à un autre.")

fichier = champ_fichier(
    "Fichier source",
    "data_convertir_fichier",
    filetypes=FILETYPES_TABLEAU,
    placeholder="C:/Users/.../donnees.csv",
)
format_sortie = st.selectbox("Format de sortie", FORMATS, index=1)

if not fichier:
    st.stop()

src = Path(fichier)
if not src.is_file():
    st.error(f"Fichier introuvable : {src}")
    st.stop()

# Aperçu rapide
try:
    import pandas as pd

    apercu = pd.read_csv(src) if src.suffix.lower() == ".csv" else (
        pd.read_excel(src) if src.suffix.lower() in (".xlsx", ".xls") else pd.read_json(src)
    )
    st.dataframe(apercu.head(20), use_container_width=True, hide_index=True)
    st.caption(f"{len(apercu)} ligne(s) × {len(apercu.columns)} colonne(s).")
except Exception as e:
    st.warning(f"Aperçu indisponible : {e}")

if st.button("Convertir", type="primary"):
    try:
        sortie = convertir_tableau(src, format_sortie)
        st.success(f"Créé : `{sortie}`")
    except Exception as e:
        st.error(str(e))
