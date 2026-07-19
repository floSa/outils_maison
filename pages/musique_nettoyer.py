from pathlib import Path

import pandas as pd
import streamlit as st

from tools.clean_library import (
    NOM_JOURNAL_NETTOYAGE,
    annuler,
    appliquer,
    previsualiser_nettoyage,
)
from ui import champ_dossier

st.title("🧼 Nettoyer la bibliothèque")
st.caption(
    "Structure attendue : `Artiste / Album / Titres`. Deux règles : les suffixes "
    "techniques des **dossiers d'album** (`(2018)`, `(Clean)`, `[UPC…]`, `{WEB}`…) sont "
    "retirés, et les **fichiers** `01. Artiste - Titre` deviennent `01 - Titre`. "
    "Aucun tag n'est lu ; rien n'est modifié tant que tu n'as pas confirmé."
)
st.info(
    "Le regroupement des « singles » est assuré par l'outil dédié "
    "**Regrouper les singles**.",
    icon="🎼",
)

racine = champ_dossier(
    "Racine de la bibliothèque", "nettoyer_racine", valeur_defaut="M:/musiques/__autres"
)

if not racine:
    st.stop()

base = Path(racine)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

if st.button("Analyser", type="primary"):
    with st.spinner("Analyse des noms…"):
        st.session_state["nettoyer_plan"] = previsualiser_nettoyage(base)
        st.session_state["nettoyer_racine"] = str(base)

plan = st.session_state.get("nettoyer_plan")
if plan is not None:
    racine = st.session_state["nettoyer_racine"]

    if not plan:
        st.success("Rien à nettoyer : tous les noms sont déjà conformes.")
    else:
        st.success(
            f"{len(plan.albums)} dossier(s) d'album et {len(plan.pistes)} fichier(s) à renommer."
        )

        if plan.albums:
            st.markdown("#### Dossiers d'album mal nommés")
            st.dataframe(
                pd.DataFrame(
                    [{"Nom actuel": r.ancien.name, "Nom cible": r.nouveau.name} for r in plan.albums]
                ),
                use_container_width=True,
                hide_index=True,
            )

        if plan.pistes:
            st.markdown("#### Fichiers mal nommés")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Album": r.ancien.parent.name,
                            "Nom actuel": r.ancien.name,
                            "Nom cible": r.nouveau.name,
                        }
                        for r in plan.pistes
                    ]
                ),
                use_container_width=True,
                hide_index=True,
                height=400,
            )

        st.divider()
        st.warning(
            "L'opération renomme des dossiers et des fichiers. Aucun fichier n'est "
            "supprimé, et un journal d'annulation est créé.",
            icon="⚠️",
        )
        if st.button("Appliquer le nettoyage", type="primary"):
            journal = appliquer(plan, racine)
            st.success(f"Nettoyage appliqué. Journal : `{journal.name}`")
            st.session_state.pop("nettoyer_plan", None)

if (base / NOM_JOURNAL_NETTOYAGE).is_file():
    st.divider()
    if st.button("↩️ Annuler le dernier nettoyage"):
        st.success(f"{annuler(base)} action(s) annulée(s).")
