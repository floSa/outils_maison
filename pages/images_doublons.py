from pathlib import Path

import streamlit as st

from tools.images import trouver_doublons
from ui import champ_dossier

st.title("👯 Trouver les doublons d'images")
st.caption("Repère les images visuellement identiques ou très proches (hash perceptuel).")

dossier = champ_dossier(
    "Dossier des images", "images_doublons_dossier", placeholder="C:/Users/.../photos"
)
col1, col2 = st.columns(2)
seuil = col1.slider("Tolérance (0 = strict, 10 = large)", 0, 10, 5)
recursif = col2.checkbox("Inclure les sous-dossiers", value=True)

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

if st.button("Rechercher", type="primary"):
    with st.spinner("Calcul des empreintes…"):
        groupes = trouver_doublons(base, recursif=recursif, seuil=seuil)

    if not groupes:
        st.success("Aucun doublon détecté 🎉")
    else:
        st.warning(f"{len(groupes)} groupe(s) de doublons.")
        for i, groupe in enumerate(groupes, 1):
            st.markdown(f"**Groupe {i}** ({len(groupe)} images)")
            cols = st.columns(min(len(groupe), 4))
            for col, img in zip(cols, groupe):
                col.image(str(img), caption=img.name, use_container_width=True)
            with st.expander("Chemins"):
                for img in groupe:
                    st.write(f"- `{img}`")
