from pathlib import Path

import streamlit as st

from tools.video import compresser

st.title("🗜️ Compresser une vidéo")
st.caption("Ré-encode en H.264 pour réduire le poids, avec redimensionnement optionnel.")

video = st.text_input("Chemin de la vidéo", placeholder="C:/Users/.../film.mov")

col1, col2 = st.columns(2)
crf = col1.slider("Qualité (CRF — bas = meilleure qualité)", 18, 32, 23)
hauteur = col2.selectbox(
    "Résolution (hauteur)", ["Originale", "1080", "720", "480"], index=0
)
preset = st.select_slider(
    "Vitesse d'encodage",
    options=["ultrafast", "fast", "medium", "slow", "veryslow"],
    value="medium",
    help="Plus lent = fichier un peu plus petit à qualité égale.",
)

if not video:
    st.stop()

src = Path(video)
if not src.is_file():
    st.error(f"Vidéo introuvable : {src}")
    st.stop()

if st.button("Compresser", type="primary"):
    with st.spinner("Compression en cours (peut être long)…"):
        try:
            sortie = compresser(
                src,
                crf=crf,
                hauteur=None if hauteur == "Originale" else int(hauteur),
                preset=preset,
            )
            taille_av = src.stat().st_size / 1e6
            taille_ap = sortie.stat().st_size / 1e6
            st.success(
                f"Créé : `{sortie}` — {taille_av:.1f} Mo → {taille_ap:.1f} Mo "
                f"({100 * (1 - taille_ap / taille_av):.0f} % de gain)"
            )
        except Exception as e:
            st.error(str(e))
