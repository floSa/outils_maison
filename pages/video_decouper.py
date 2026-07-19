from pathlib import Path

import streamlit as st

from tools.ffmpeg_utils import duree_secondes
from tools.video import decouper
from ui import FILETYPES_VIDEO, champ_fichier

st.title("✂️ Découper une vidéo")
st.caption("Extrait un passage d'une vidéo, sans ré-encodage (rapide, sans perte).")

video = champ_fichier(
    "Chemin de la vidéo",
    "video_decouper_video",
    filetypes=FILETYPES_VIDEO,
    placeholder="C:/Users/.../film.mp4",
)

if not video:
    st.stop()

src = Path(video)
if not src.is_file():
    st.error(f"Vidéo introuvable : {src}")
    st.stop()

duree = duree_secondes(src)
if duree:
    m, s = divmod(int(duree), 60)
    h, m = divmod(m, 60)
    st.info(f"Durée : {h:02d}:{m:02d}:{s:02d}")

col1, col2 = st.columns(2)
debut = col1.text_input("Début (HH:MM:SS)", value="00:00:00")
fin = col2.text_input("Fin (HH:MM:SS)", value="00:00:10")
nom_sortie = st.text_input("Nom de sortie (vide = <nom>_extrait)", value="")

if st.button("Découper", type="primary"):
    with st.spinner("Découpage…"):
        try:
            sortie = decouper(src, debut, fin, src.with_name(nom_sortie) if nom_sortie else None)
            st.success(f"Extrait créé : `{sortie}`")
        except Exception as e:
            st.error(str(e))
