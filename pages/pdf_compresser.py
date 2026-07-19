from pathlib import Path

import streamlit as st

from tools.pdf import compresser
from ui import FILETYPES_PDF, champ_fichier

st.title("🗜️ Compresser un PDF")
st.caption("Réduit le poids d'un PDF (déflation des flux, nettoyage des objets inutiles).")

chemin = champ_fichier(
    "Chemin du PDF",
    "pdf_compresser_chemin",
    filetypes=FILETYPES_PDF,
    placeholder="C:/Users/.../document.pdf",
)

if not chemin:
    st.stop()

src = Path(chemin)
if not src.is_file():
    st.error(f"PDF introuvable : {src}")
    st.stop()

if st.button("Compresser", type="primary"):
    with st.spinner("Compression…"):
        try:
            sortie = compresser(src)
            av = src.stat().st_size / 1e6
            ap = sortie.stat().st_size / 1e6
            gain = 100 * (1 - ap / av) if av else 0
            st.success(f"Créé : `{sortie}` — {av:.2f} Mo → {ap:.2f} Mo ({gain:.0f} % de gain)")
        except Exception as e:
            st.error(str(e))
