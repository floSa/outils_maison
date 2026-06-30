from pathlib import Path

import streamlit as st

from tools.audio import CODECS_AUDIO, EXT_AUDIO, convertir_audio

st.title("🎚️ Convertir un format audio")
st.caption("Convertit un fichier (ou tout un dossier) vers un autre format audio.")

chemin = st.text_input("Fichier audio ou dossier", placeholder="M:/musiques/album")
col1, col2 = st.columns(2)
format_sortie = col1.selectbox("Format de sortie", list(CODECS_AUDIO), index=1)
bitrate = col2.text_input("Bitrate (mp3/m4a, ex. 320k — vide = défaut)", value="")

if not chemin:
    st.stop()

p = Path(chemin)
if p.is_dir():
    cibles = sorted(f for f in p.iterdir() if f.suffix.lower() in EXT_AUDIO)
elif p.is_file():
    cibles = [p]
else:
    st.error(f"Chemin introuvable : {p}")
    st.stop()

st.write(f"{len(cibles)} fichier(s) à convertir.")
if cibles and st.button("Convertir", type="primary"):
    with st.status("Conversion…", expanded=True) as status:
        ok = 0
        for f in cibles:
            try:
                st.write(f"→ {f.name}")
                convertir_audio(f, format_sortie, bitrate=bitrate or None)
                ok += 1
            except Exception as e:
                st.write(f"   ❌ {e}")
        status.update(label=f"Terminé — {ok}/{len(cibles)} ✅", state="complete")
