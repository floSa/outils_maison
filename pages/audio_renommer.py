from pathlib import Path

import pandas as pd
import streamlit as st

from tools.audio import previsualiser_renommage_tags
from tools.files import NOM_JOURNAL, annuler, appliquer

st.title("🏷️ Renommer l'audio depuis les tags")
st.caption("Construit les noms de fichiers à partir des métadonnées (artiste, titre, piste…).")

dossier = st.text_input("Dossier audio", placeholder="M:/musiques/album")
motif = st.text_input(
    "Motif du nom",
    value="{piste} - {artiste} - {titre}",
    help="Champs : {piste} {artiste} {titre} {album} {annee}",
)
recursif = st.checkbox("Inclure les sous-dossiers", value=False)

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

renommages = previsualiser_renommage_tags(base, motif, recursif=recursif)

st.markdown("#### Aperçu")
if not renommages:
    st.info("Aucun renommage à proposer (tags manquants ou noms déjà conformes).")
else:
    df = pd.DataFrame(
        [{"Avant": r.ancien.name, "Après": r.nouveau.name} for r in renommages]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    if st.button(f"Renommer {len(renommages)} fichier(s)", type="primary"):
        journal = appliquer(renommages, base)
        st.success(f"Renommage effectué. Annulation possible (journal : `{journal.name}`).")

st.divider()
if (base / NOM_JOURNAL).is_file():
    if st.button("Annuler le dernier renommage"):
        st.success(f"{annuler(base)} fichier(s) restauré(s).")
