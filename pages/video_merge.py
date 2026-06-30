from pathlib import Path

import streamlit as st

from tools.video import fusionner_videos, lister_videos

st.title("🎬 Fusionner des vidéos")
st.caption("Concatène tous les clips d'un dossier, dans l'ordre alphabétique.")

dossier = st.text_input("Dossier des vidéos", placeholder="C:/Users/.../clips")
motif = st.text_input("Motif de fichiers", value="*.mp4")

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

videos = lister_videos(base, motif)
if not videos:
    st.warning(f"Aucune vidéo « {motif} » dans ce dossier.")
    st.stop()

st.success(f"{len(videos)} vidéo(s) — elles seront fusionnées dans cet ordre :")
for i, v in enumerate(videos, 1):
    st.write(f"{i}. {v.name}")

nom_sortie = st.text_input("Nom du fichier fusionné", value="compile.mp4")

if st.button("Fusionner", type="primary"):
    with st.status("Fusion en cours…", expanded=True) as status:
        try:
            sortie = fusionner_videos(
                base, nom_sortie, motif=motif, log=lambda m: st.write(m)
            )
            status.update(label="Terminé ✅", state="complete")
            st.success(f"Fichier créé : `{sortie}`")
        except Exception as e:
            status.update(label="Échec ❌", state="error")
            st.error(f"Erreur lors de la fusion : {e}")
