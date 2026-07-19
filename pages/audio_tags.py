from pathlib import Path

import streamlit as st

from tools.audio import editer_tags
from ui import champ_dossier

st.title("🏷️ Éditer les tags en masse")
st.caption("Applique des métadonnées communes à tous les fichiers audio d'un dossier.")

dossier = champ_dossier(
    "Dossier audio", "audio_tags_dossier", placeholder="M:/musiques/album"
)
recursif = st.checkbox("Inclure les sous-dossiers", value=False)

st.markdown("#### Champs à appliquer (laisser vide pour ne pas toucher)")
col1, col2 = st.columns(2)
artist = col1.text_input("Artiste")
albumartist = col2.text_input("Artiste de l'album")
album = col1.text_input("Album")
date = col2.text_input("Année")
genre = col1.text_input("Genre")

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

tags = {
    "artist": artist,
    "albumartist": albumartist,
    "album": album,
    "date": date,
    "genre": genre,
}
actifs = {k: v for k, v in tags.items() if v}

if not actifs:
    st.info("Renseigne au moins un champ.")
    st.stop()

st.write("Seront appliqués :", actifs)
if st.button("Appliquer les tags", type="primary"):
    n = editer_tags(base, tags, recursif=recursif)
    st.success(f"{n} fichier(s) mis à jour.")
