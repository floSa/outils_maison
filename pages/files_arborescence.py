from pathlib import Path

import streamlit as st

from tools.files import arborescence_vers_df, exporter_excel
from ui import champ_fichier_sortie, choisir_dossier

st.title("🌳 Arborescence → Excel")
st.caption("Cartographie l'arborescence d'un ou plusieurs dossiers dans un tableau exportable.")

if "arbo_dossiers" not in st.session_state:
    st.session_state["arbo_dossiers"] = []

st.markdown("**Dossiers à explorer**")
if st.button("📂 Ajouter un dossier", key="arbo_ajouter"):
    chemin = choisir_dossier(titre="Ajouter un dossier à explorer")
    if chemin and chemin not in st.session_state["arbo_dossiers"]:
        st.session_state["arbo_dossiers"].append(chemin)
        st.rerun()

if not st.session_state["arbo_dossiers"]:
    st.caption("Aucun dossier sélectionné")
for i, dossier in enumerate(st.session_state["arbo_dossiers"]):
    col_chemin, col_retirer = st.columns([6, 0.6], vertical_alignment="center")
    col_chemin.code(dossier, language=None, wrap_lines=True)
    if col_retirer.button("✕", key=f"arbo_retirer_{i}", help="Retirer ce dossier"):
        st.session_state["arbo_dossiers"].pop(i)
        st.rerun()

col1, col2 = st.columns(2)
profondeur = col1.number_input("Profondeur max (0 = illimitée)", value=0, min_value=0, step=1)
inclure_fichiers = col2.checkbox("Inclure les fichiers", value=False)

if not st.session_state["arbo_dossiers"]:
    st.stop()

racines = [Path(d) for d in st.session_state["arbo_dossiers"]]
for r in [r for r in racines if not r.is_dir()]:
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
    chemin = champ_fichier_sortie(
        "Chemin du fichier Excel",
        "files_arbo_export",
        valeur_defaut=str(Path.home() / "Desktop" / "arborescence.xlsx"),
        filetypes=[("Excel", "*.xlsx"), ("Tous les fichiers", "*.*")],
    )
    if st.button("Exporter en Excel"):
        try:
            cible = exporter_excel(df, chemin)
            st.success(f"Exporté : `{cible}`")
        except Exception as e:
            st.error(str(e))
