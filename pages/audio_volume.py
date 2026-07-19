from pathlib import Path

import streamlit as st

from tools.audio import EXT_AUDIO, normaliser_volume
from ui import champ_mixte

st.title("🔊 Normaliser le volume")
st.caption("Égalise le volume perçu (norme EBU R128 / loudnorm) vers une cible commune.")

chemin = champ_mixte(
    "Fichier audio ou dossier", "audio_volume_chemin", placeholder="M:/musiques/album"
)
cible_lufs = st.slider(
    "Cible (LUFS)", -24.0, -9.0, -14.0, 0.5,
    help="-14 LUFS ≈ standard streaming. Plus bas = plus fort.",
)

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

st.write(f"{len(cibles)} fichier(s) à traiter (un fichier `_norm` est créé à côté).")
if cibles and st.button("Normaliser", type="primary"):
    with st.status("Normalisation…", expanded=True) as status:
        ok = 0
        for f in cibles:
            try:
                st.write(f"→ {f.name}")
                normaliser_volume(f, cible_lufs=cible_lufs)
                ok += 1
            except Exception as e:
                st.write(f"   ❌ {e}")
        status.update(label=f"Terminé — {ok}/{len(cibles)} ✅", state="complete")
