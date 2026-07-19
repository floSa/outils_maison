from pathlib import Path

import pandas as pd
import streamlit as st

from tools.pdf import Segment, compter_pages, extraire_segments
from ui import FILETYPES_PDF, champ_dossier, champ_fichier

st.title("✂️ Extraire des pages d'un PDF")
st.caption("Découpe un PDF source en plusieurs documents selon des plages de pages.")

pdf_path = champ_fichier(
    "Chemin du PDF source",
    "pdf_extract_source",
    filetypes=FILETYPES_PDF,
    placeholder="C:/Users/.../document.pdf",
)

if not pdf_path:
    st.stop()

source = Path(pdf_path)
if not source.is_file():
    st.error(f"Fichier introuvable : {source}")
    st.stop()

try:
    nb_pages = compter_pages(source)
except Exception as e:  # PDF corrompu, chiffré…
    st.error(f"Impossible de lire le PDF : {e}")
    st.stop()

st.success(f"PDF valide — **{nb_pages} pages**.")

st.markdown("#### Plages à extraire")
st.caption("Numéros de pages 1-indexés, **fin incluse**. Une ligne = un fichier produit.")

defaut = pd.DataFrame(
    [{"nom": "extrait_1", "debut": 1, "fin": min(nb_pages, 1)}]
)
table = st.data_editor(
    defaut,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "nom": st.column_config.TextColumn("Nom du fichier", required=True),
        "debut": st.column_config.NumberColumn("Début", min_value=1, max_value=nb_pages, step=1),
        "fin": st.column_config.NumberColumn("Fin", min_value=1, max_value=nb_pages, step=1),
    },
)

dossier_sortie = champ_dossier(
    "Dossier de sortie (vide = dossier du PDF source)", "pdf_extract_dossier_sortie"
)

if st.button("Extraire", type="primary"):
    segments = [
        Segment(nom=str(r["nom"]), debut=int(r["debut"]), fin=int(r["fin"]))
        for _, r in table.iterrows()
        if str(r["nom"]).strip()
    ]
    if not segments:
        st.warning("Aucune plage valide à extraire.")
        st.stop()

    res = extraire_segments(
        source, segments, dossier_sortie=dossier_sortie or None
    )
    for av in res.avertissements:
        st.warning(av)
    if res.crees:
        st.success(f"{len(res.crees)} fichier(s) créé(s) :")
        for p in res.crees:
            st.write(f"- `{p}`")
