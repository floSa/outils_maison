from pathlib import Path

import streamlit as st

from tools.files import comparer_dossiers

st.title("🔀 Comparer deux dossiers")
st.caption("Liste ce qui diffère entre deux arborescences (par chemin relatif).")

col1, col2 = st.columns(2)
dossier_a = col1.text_input("Dossier A", placeholder="C:/.../original")
dossier_b = col2.text_input("Dossier B", placeholder="C:/.../copie")
par_hash = st.checkbox("Comparer le contenu (SHA-1, plus lent)", value=False)

if not dossier_a or not dossier_b:
    st.stop()

if not Path(dossier_a).is_dir() or not Path(dossier_b).is_dir():
    st.error("Les deux dossiers doivent exister.")
    st.stop()

if st.button("Comparer", type="primary"):
    with st.spinner("Comparaison…"):
        res = comparer_dossiers(dossier_a, dossier_b, par_hash=par_hash)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Seulement dans A", len(res["seulement_a"]))
    c2.metric("Seulement dans B", len(res["seulement_b"]))
    c3.metric("Différents", len(res["differents"]))
    c4.metric("Identiques", res["identiques"])

    def _liste(titre, items):
        if items:
            with st.expander(f"{titre} ({len(items)})"):
                for x in items:
                    st.write(f"- `{x}`")

    _liste("Seulement dans A", res["seulement_a"])
    _liste("Seulement dans B", res["seulement_b"])
    _liste("Différents (présents des deux côtés)", res["differents"])
