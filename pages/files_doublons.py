from pathlib import Path

import streamlit as st

from tools.files import trouver_doublons_fichiers

st.title("🧬 Trouver les fichiers en double")
st.caption("Détecte les fichiers strictement identiques (même contenu) par empreinte SHA-1.")

dossier = st.text_input("Dossier à analyser", placeholder="C:/Users/.../dossier")
recursif = st.checkbox("Inclure les sous-dossiers", value=True)

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

if st.button("Rechercher", type="primary"):
    with st.spinner("Analyse…"):
        groupes = trouver_doublons_fichiers(base, recursif=recursif)

    if not groupes:
        st.success("Aucun doublon détecté 🎉")
    else:
        total = sum(len(g) - 1 for g in groupes)
        st.warning(f"{len(groupes)} groupe(s) — {total} fichier(s) en trop.")
        for i, groupe in enumerate(groupes, 1):
            with st.expander(f"Groupe {i} — {len(groupe)} copies ({groupe[0].name})"):
                for f in groupe:
                    taille = f.stat().st_size / 1024
                    st.write(f"- `{f}` ({taille:.0f} Ko)")
