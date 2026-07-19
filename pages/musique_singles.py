from pathlib import Path

import pandas as pd
import streamlit as st

from tools.musique import (
    NOM_DOSSIER_SINGLES,
    NOM_JOURNAL,
    analyser,
    annuler,
    appliquer,
    previsualiser,
)
from ui import champ_dossier

st.title("🎼 Regrouper les singles")
st.caption(
    "Parcourt une bibliothèque (racine → artistes → albums) et regroupe chaque album "
    "à un seul titre dans un dossier `Singles/` par artiste, puis supprime le dossier vidé."
)

racine = champ_dossier(
    "Dossier racine de la bibliothèque", "musique_singles_racine", placeholder="M:/musiques"
)

if st.button("Analyser", type="primary"):
    base = Path(racine)
    if not base.is_dir():
        st.error(f"Dossier introuvable : {base}")
        st.stop()
    with st.spinner("Analyse de l'arborescence…"):
        st.session_state["singles_plan"] = analyser(base)
        st.session_state["singles_racine"] = str(base)

plan = st.session_state.get("singles_plan")
if not plan:
    st.stop()

racine = st.session_state["singles_racine"]
st.success(
    f"{len(plan.a_traiter)} single(s) à regrouper · "
    f"{len(plan.a_verifier)} dossier(s) à vérifier (laissés tels quels)."
)

if plan.a_traiter:
    st.markdown("#### À regrouper")
    mouvements = previsualiser(plan)
    lignes = []
    for sa, mv in zip(plan.a_traiter, mouvements):
        lignes.append(
            {
                "Artiste": sa.artiste.name,
                "Album (sera supprimé)": sa.album.name,
                "Titre → Singles/": mv.audio_dst.name,
                "Cover → Singles/": mv.cover_dst.name if mv.cover_dst else "—",
            }
        )
    st.dataframe(pd.DataFrame(lignes), use_container_width=True, hide_index=True)

if plan.a_verifier:
    with st.expander(f"⚠️ {len(plan.a_verifier)} dossier(s) à vérifier (non traités)"):
        for sa in plan.a_verifier:
            extras = ", ".join(p.name for p in sa.autres)
            st.write(f"- `{sa.artiste.name}/{sa.album.name}` — contenu en plus : {extras}")

st.divider()
if plan.a_traiter:
    st.warning(
        "L'opération **déplace** les fichiers et **supprime** les dossiers album vidés. "
        "Un journal d'annulation est créé.",
        icon="⚠️",
    )
    if st.button(f"Regrouper {len(plan.a_traiter)} single(s)", type="primary"):
        with st.status("Déplacement…", expanded=True) as status:
            journal = appliquer(plan, racine, log=lambda m: st.write(m))
            status.update(label="Terminé ✅", state="complete")
        st.success(f"Regroupement effectué. Journal : `{journal.name}`")
        st.session_state.pop("singles_plan", None)

if (Path(racine) / NOM_JOURNAL).is_file():
    st.divider()
    if st.button("↩️ Annuler le dernier regroupement"):
        n = annuler(racine)
        st.success(f"{n} action(s) annulée(s).")
