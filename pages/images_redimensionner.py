from pathlib import Path

import streamlit as st

from tools.images import lister_images, redimensionner

st.title("📐 Redimensionner / compresser des images")
st.caption("Réduit la taille d'un lot d'images (ratio conservé) et les compresse.")

dossier = st.text_input("Dossier des images", placeholder="C:/Users/.../photos")
col1, col2, col3 = st.columns(3)
largeur_max = col1.number_input("Largeur max (px, 0 = auto)", value=1920, step=100)
hauteur_max = col2.number_input("Hauteur max (px, 0 = auto)", value=0, step=100)
qualite = col3.slider("Qualité", 50, 100, 85)

recursif = st.checkbox("Inclure les sous-dossiers", value=False)
sous_dossier = st.text_input("Sous-dossier de sortie", value="redimensionnees")

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

images = lister_images(base, recursif=recursif)
st.write(f"{len(images)} image(s) trouvée(s).")

if images and st.button("Redimensionner", type="primary"):
    sortie = base / sous_dossier
    with st.status("Traitement…", expanded=True) as status:
        ok = 0
        for img in images:
            try:
                dest = sortie / img.relative_to(base)
                redimensionner(
                    img,
                    dest,
                    largeur_max=int(largeur_max) or None,
                    hauteur_max=int(hauteur_max) or None,
                    qualite=qualite,
                )
                ok += 1
            except Exception as e:
                st.write(f"❌ {img.name} : {e}")
        status.update(label=f"Terminé — {ok}/{len(images)} ✅", state="complete")
        st.success(f"Images écrites dans `{sortie}`.")
