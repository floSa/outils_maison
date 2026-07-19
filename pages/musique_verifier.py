from pathlib import Path

import pandas as pd
import streamlit as st

from tools.clean_library import verifier_titres
from ui import champ_dossier

st.title("🔍 Vérifier les titres")
st.caption(
    "Contrôle **en lecture seule** : liste les fichiers dont le titre n'est pas « seul » "
    "— il contient encore le nom de l'artiste ou de l'album, ou reste au format "
    "`numéro. Artiste - Titre`. Aucun fichier n'est modifié."
)

racine = champ_dossier(
    "Racine de la bibliothèque", "verifier_racine", valeur_defaut="M:/musiques/__autres"
)

if not racine:
    st.stop()

base = Path(racine)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

if st.button("Vérifier", type="primary"):
    with st.spinner("Analyse des titres…"):
        st.session_state["verifier_resultats"] = verifier_titres(base)

resultats = st.session_state.get("verifier_resultats")
if resultats is None:
    st.stop()

if not resultats:
    st.success("Tous les titres sont propres : aucun ne contient l'artiste ni l'album.")
else:
    st.warning(f"{len(resultats)} titre(s) à revoir.")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Artiste": t.artiste,
                    "Album": t.album,
                    "Fichier": t.fichier.name,
                    "Pourquoi": ", ".join(t.raisons),
                }
                for t in resultats
            ]
        ),
        use_container_width=True,
        hide_index=True,
        height=400,
    )
    st.caption(
        "Pour corriger automatiquement, utilise l'outil **Nettoyer la bibliothèque**."
    )
