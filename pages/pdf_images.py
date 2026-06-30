from pathlib import Path

import streamlit as st

from tools.images import lister_images, tri_naturel
from tools.pdf import images_vers_pdf, pdf_vers_images

st.title("🖼️ Images ↔ PDF")
st.caption("Assemble des images en PDF, ou exporte les pages d'un PDF en images.")

sens = st.radio("Sens de conversion", ["Images → PDF", "PDF → Images"], horizontal=True)

if sens == "Images → PDF":
    dossier = st.text_input("Dossier des images", placeholder="C:/Users/.../scans")
    nom_sortie = st.text_input("Nom du PDF", value="document.pdf")
    if not dossier:
        st.stop()
    base = Path(dossier)
    if not base.is_dir():
        st.error(f"Dossier introuvable : {base}")
        st.stop()
    imgs = tri_naturel(lister_images(base))
    st.write(f"{len(imgs)} image(s) — assemblées dans l'ordre naturel.")
    if imgs and st.button("Créer le PDF", type="primary"):
        try:
            sortie = images_vers_pdf(imgs, base / nom_sortie)
            st.success(f"PDF créé : `{sortie}`")
        except Exception as e:
            st.error(str(e))

else:
    pdf = st.text_input("Chemin du PDF", placeholder="C:/Users/.../document.pdf")
    col1, col2 = st.columns(2)
    dpi = col1.slider("Résolution (DPI)", 72, 300, 150)
    fmt = col2.selectbox("Format des images", ["png", "jpg"], index=0)
    if not pdf:
        st.stop()
    src = Path(pdf)
    if not src.is_file():
        st.error(f"PDF introuvable : {src}")
        st.stop()
    if st.button("Exporter les pages", type="primary"):
        with st.spinner("Rendu des pages…"):
            try:
                sorties = pdf_vers_images(src, dpi=dpi, format_image=fmt)
                st.success(f"{len(sorties)} image(s) créée(s) dans `{sorties[0].parent}`.")
            except Exception as e:
                st.error(str(e))
