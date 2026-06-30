from pathlib import Path

import streamlit as st

from tools.images import convertir, lister_images

st.title("🔄 Convertir des images")
st.caption("Convertit un lot d'images vers un autre format. Gère le HEIC (photos iPhone) en entrée.")

dossier = st.text_input("Dossier des images", placeholder="C:/Users/.../photos")
col1, col2 = st.columns(2)
format_sortie = col1.selectbox("Format de sortie", ["jpg", "png", "webp"], index=0)
qualite = col2.slider("Qualité (jpg/webp)", 50, 100, 90)
recursif = st.checkbox("Inclure les sous-dossiers", value=False)

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

images = lister_images(base, recursif=recursif)
st.write(f"{len(images)} image(s) trouvée(s).")

if images and st.button("Convertir", type="primary"):
    with st.status("Conversion…", expanded=True) as status:
        ok = 0
        for img in images:
            if img.suffix.lower() == f".{format_sortie}":
                continue
            try:
                convertir(img, format_sortie, qualite=qualite)
                ok += 1
            except Exception as e:
                st.write(f"❌ {img.name} : {e}")
        status.update(label=f"Terminé — {ok} converti(s) ✅", state="complete")
