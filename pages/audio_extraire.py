from pathlib import Path

import streamlit as st

from tools.audio import CODECS_AUDIO, EXT_VIDEO, extraire_audio
from ui import champ_mixte

st.title("🎵 Extraire l'audio d'une vidéo")
st.caption("Récupère la piste audio d'une (ou plusieurs) vidéo dans le format de ton choix.")

dossier_ou_fichier = champ_mixte(
    "Chemin d'une vidéo ou d'un dossier de vidéos",
    "audio_extraire_chemin",
    placeholder="C:/Users/.../clip.mp4",
)
format_sortie = st.selectbox("Format de sortie", list(CODECS_AUDIO), index=0)

if not dossier_ou_fichier:
    st.stop()

chemin = Path(dossier_ou_fichier)
if chemin.is_dir():
    cibles = sorted(f for f in chemin.iterdir() if f.suffix.lower() in EXT_VIDEO)
elif chemin.is_file():
    cibles = [chemin]
else:
    st.error(f"Chemin introuvable : {chemin}")
    st.stop()

if not cibles:
    st.warning("Aucune vidéo trouvée.")
    st.stop()

st.write(f"{len(cibles)} vidéo(s) à traiter.")

if st.button("Extraire", type="primary"):
    with st.status("Extraction…", expanded=True) as status:
        ok = 0
        for v in cibles:
            try:
                st.write(f"→ {v.name}")
                sortie = extraire_audio(v, format_sortie)
                st.write(f"   ✅ {sortie.name}")
                ok += 1
            except Exception as e:
                st.write(f"   ❌ {e}")
        status.update(label=f"Terminé — {ok}/{len(cibles)} ✅", state="complete")
