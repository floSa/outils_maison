from pathlib import Path

import pandas as pd
import streamlit as st

from tools.files import NOM_JOURNAL, annuler, appliquer, previsualiser_rangement

st.title("🗂️ Ranger automatiquement")
st.caption("Déplace les fichiers d'un dossier dans des sous-dossiers par type ou par date.")

dossier = st.text_input("Dossier à ranger", placeholder="C:/Users/.../Telechargements")
mode = st.radio("Critère", ["type", "date"], horizontal=True,
                format_func=lambda m: "Par type" if m == "type" else "Par date (année/mois)")

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

renommages = previsualiser_rangement(base, mode=mode)

st.markdown("#### Aperçu")
if not renommages:
    st.info("Rien à ranger (aucun fichier à la racine du dossier).")
else:
    df = pd.DataFrame(
        [{"Fichier": r.ancien.name, "Vers": str(r.nouveau.relative_to(base))} for r in renommages]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    if st.button(f"Ranger {len(renommages)} fichier(s)", type="primary"):
        journal = appliquer(renommages, base)
        st.success(f"Rangement effectué (journal : `{journal.name}`).")

st.divider()
if (base / NOM_JOURNAL).is_file():
    if st.button("Annuler le dernier rangement"):
        st.success(f"{annuler(base)} fichier(s) restauré(s).")
