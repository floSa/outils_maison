from pathlib import Path

import pandas as pd
import streamlit as st

from tools.files import statistiques
from ui import champ_dossier


def _human(n: int) -> str:
    for unite in ("o", "Ko", "Mo", "Go", "To"):
        if n < 1024:
            return f"{n:.0f} {unite}" if unite == "o" else f"{n:.1f} {unite}"
        n /= 1024
    return f"{n:.1f} Po"


st.title("📊 Statistiques d'un dossier")
st.caption("Volume par catégorie, plus gros fichiers, dossiers vides.")

dossier = champ_dossier(
    "Dossier à analyser", "files_stats_dossier", placeholder="M:/musiques"
)
recursif = st.checkbox("Inclure les sous-dossiers", value=True)

if not dossier:
    st.stop()

base = Path(dossier)
if not base.is_dir():
    st.error(f"Dossier introuvable : {base}")
    st.stop()

if st.button("Analyser", type="primary"):
    with st.spinner("Analyse…"):
        stats = statistiques(base, recursif=recursif)
    st.session_state["stats"] = stats

stats = st.session_state.get("stats")
if not stats:
    st.stop()

c1, c2 = st.columns(2)
c1.metric("Fichiers", stats["nb_fichiers"])
c2.metric("Taille totale", _human(stats["taille_totale"]))

st.markdown("#### Par catégorie")
cat = pd.DataFrame(
    [{"Catégorie": k, "Fichiers": v[0], "Taille": _human(v[1])} for k, v in stats["par_categorie"].items()]
).sort_values("Fichiers", ascending=False)
st.dataframe(cat, use_container_width=True, hide_index=True)

st.markdown("#### Plus gros fichiers")
gros = pd.DataFrame([{"Fichier": p.name, "Taille": _human(t), "Chemin": str(p)} for p, t in stats["plus_gros"]])
st.dataframe(gros, use_container_width=True, hide_index=True)

if stats["dossiers_vides"]:
    with st.expander(f"📁 {len(stats['dossiers_vides'])} dossier(s) vide(s)"):
        for d in stats["dossiers_vides"]:
            st.write(f"- `{d}`")
