from pathlib import Path

import streamlit as st

from tools.files import arborescence_vers_df, exporter_excel

st.title("🌳 Arborescence → Excel")
st.caption("Cartographie l'arborescence d'un ou plusieurs dossiers dans un tableau exportable.")

saisie = st.text_area(
    "Dossiers à explorer (un par ligne)",
    placeholder="M:/musiques\nE:/films",
    height=100,
)
col1, col2 = st.columns(2)
profondeur = col1.number_input("Profondeur max (0 = illimitée)", value=0, min_value=0, step=1)
inclure_fichiers = col2.checkbox("Inclure les fichiers", value=False)

if not saisie.strip():
    st.stop()

racines = [Path(l.strip()) for l in saisie.splitlines() if l.strip()]
absents = [r for r in racines if not r.is_dir()]
for r in absents:
    st.warning(f"Dossier introuvable (ignoré) : {r}")

if st.button("Explorer", type="primary"):
    with st.spinner("Exploration…"):
        df = arborescence_vers_df(
            racines,
            profondeur_max=int(profondeur) or None,
            inclure_fichiers=inclure_fichiers,
        )
    if df.empty:
        st.info("Rien à afficher.")
    else:
        st.session_state["arbo_df"] = df

if "arbo_df" in st.session_state:
    df = st.session_state["arbo_df"]
    st.write(f"{len(df)} ligne(s).")
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)
    chemin = st.text_input(
        "Chemin du fichier Excel", value=str(Path.home() / "Desktop" / "arborescence.xlsx")
    )
    if st.button("Exporter en Excel"):
        try:
            cible = exporter_excel(df, chemin)
            st.success(f"Exporté : `{cible}`")
        except Exception as e:
            st.error(str(e))
