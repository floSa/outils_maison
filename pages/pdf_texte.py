from pathlib import Path

import streamlit as st

from tools.pdf import extraire_texte

st.title("📝 Extraire le texte d'un PDF")
st.caption("Récupère le texte intégré d'un PDF vers un fichier .txt (sans OCR).")

chemin = st.text_input("Chemin du PDF", placeholder="C:/Users/.../document.pdf")

if not chemin:
    st.stop()

src = Path(chemin)
if not src.is_file():
    st.error(f"PDF introuvable : {src}")
    st.stop()

if st.button("Extraire le texte", type="primary"):
    try:
        sortie, semble_scanne = extraire_texte(src)
        st.success(f"Texte écrit dans `{sortie}`")
        if semble_scanne:
            st.warning(
                "Très peu de texte trouvé : ce PDF est probablement scanné (images). "
                "Un OCR (hors de cet outil) serait nécessaire.",
                icon="🔍",
            )
        apercu = sortie.read_text(encoding="utf-8")[:2000]
        if apercu.strip():
            st.text_area("Aperçu", apercu, height=300)
    except Exception as e:
        st.error(str(e))
