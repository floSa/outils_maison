from pathlib import Path

import streamlit as st

from tools.pdf import fusionner
from ui import champ_dossier

st.title("📚 Fusionner des PDF")
st.caption("Concatène plusieurs PDF en un seul, dans l'ordre choisi.")

dossier = champ_dossier(
    "Dossier contenant les PDF", "pdf_fusionner_dossier", placeholder="C:/Users/.../docs"
)

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

pdfs = sorted(base.glob("*.pdf"))
if not pdfs:
    st.warning("Aucun PDF dans ce dossier.")
    st.stop()

st.markdown("#### Ordre de fusion")
st.caption("Décoche pour exclure ; l'ordre suit la liste (alphabétique).")
choisis = [p for p in pdfs if st.checkbox(p.name, value=True, key=str(p))]

nom_sortie = st.text_input("Nom du fichier fusionné", value="fusion.pdf")

if st.button("Fusionner", type="primary") and choisis:
    try:
        sortie = fusionner(choisis, base / nom_sortie)
        st.success(f"PDF fusionné : `{sortie}`")
    except Exception as e:
        st.error(str(e))
