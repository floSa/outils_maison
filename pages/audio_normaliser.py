from pathlib import Path

import streamlit as st

from tools.audio import normaliser_dossier

st.title("🎚️ Normaliser des FLAC")
st.caption("Ré-encode les FLAC haute résolution en 16 bit / 44.1 kHz, tags préservés.")

st.warning("Les fichiers sont modifiés **sur place**. Fais une sauvegarde si besoin.", icon="⚠️")

dossier = st.text_input("Dossier des FLAC", placeholder="M:/musiques/album")
recursif = st.checkbox("Inclure les sous-dossiers", value=True)

col1, col2 = st.columns(2)
sr_max = col1.number_input("Fréquence cible (Hz)", value=44100, step=100)
bits_max = col2.selectbox("Profondeur cible (bits)", [16, 24], index=0)

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

if st.button("Normaliser", type="primary"):
    with st.status("Analyse et normalisation…", expanded=True) as status:
        try:
            traites = normaliser_dossier(
                base,
                recursif=recursif,
                sr_max=int(sr_max),
                bits_max=int(bits_max),
                log=lambda m: st.write(m),
            )
            status.update(label="Terminé ✅", state="complete")
            if traites:
                st.success(f"{len(traites)} fichier(s) normalisé(s).")
            else:
                st.info("Aucun fichier à normaliser (tout est déjà conforme).")
        except Exception as e:
            status.update(label="Échec ❌", state="error")
            st.error(str(e))
