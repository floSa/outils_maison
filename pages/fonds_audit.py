from pathlib import Path

import pandas as pd
import streamlit as st

st.title("🔎 Auditer le dossier trié (Fonds_Tries)")
st.caption(
    "Repère les couples paysage/portrait probablement mal classés : un portrait qui "
    "ressemble bien plus à un autre paysage qu'au sien."
)

try:
    import cv2  # noqa: F401

    from tools import fonds
except ModuleNotFoundError:
    st.warning(
        "Cet outil nécessite l'extra **vision** (OpenCV) : `uv sync --extra vision`.",
        icon="📦",
    )
    st.stop()

DEFAUT = "C:/Users/FLORIAN/Pictures/FDE/Fonds_Tries"
dossier = st.text_input("Dossier trié", value=DEFAUT)
seuil = st.slider(
    "Seuil « suspect » (score propre en dessous duquel on vérifie en profondeur)",
    10, 80, fonds.SEUIL_INLIERS,
)

st.info(
    "L'audit calcule d'abord le score de chaque couple (rapide), puis ne cherche le "
    "vrai paysage que pour les couples au score faible. Sur une grande bibliothèque, "
    "la 1ʳᵉ passe peut prendre quelques minutes.",
    icon="⏱️",
)

if st.button("Lancer l'audit", type="primary"):
    base = Path(dossier)
    if not base.is_dir():
        st.error(f"Dossier introuvable : {base}")
        st.stop()
    with st.status("Audit en cours…", expanded=True) as status:
        suspects = fonds.auditer(base, seuil_suspect=seuil, log=lambda m: st.write(m))
        status.update(label="Audit terminé ✅", state="complete")
    st.session_state["audit"] = suspects

suspects = st.session_state.get("audit")
if suspects is None:
    st.stop()

erreurs = [s for s in suspects if s.probable_erreur]
st.success(f"{len(suspects)} couple(s) à score faible — dont {len(erreurs)} erreur(s) probable(s).")

if suspects:
    df = pd.DataFrame(
        [
            {
                "Couple": s.ident,
                "Score propre": s.score_propre,
                "Meilleur paysage": s.meilleur_ident,
                "Score": s.meilleur_score,
                "Erreur probable": "⚠️ oui" if s.probable_erreur else "—",
            }
            for s in suspects
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(
        "« Erreur probable » = le portrait correspond bien mieux au paysage d'un autre "
        "couple. À vérifier visuellement, l'audit ne renomme rien."
    )
