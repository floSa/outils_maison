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

from ui import champ_dossier

DEFAUT = "C:/Users/FLORIAN/Pictures/FDE/Fonds_Tries"
dossier = champ_dossier("Dossier trié", "fonds_audit_dossier", valeur_defaut=DEFAUT)
seuil = st.slider(
    "Seuil « suspect » (score propre en dessous duquel on vérifie en profondeur)",
    10, 80, fonds.SEUIL_INLIERS,
)

col1, col2 = st.columns(2)
lancer = col1.button("Lancer l'audit (long)", type="primary")
charger = col2.button("Charger le dernier audit")

st.info(
    "L'audit calcule d'abord le score de chaque couple (rapide), puis ne cherche le "
    "vrai paysage que pour les couples au score faible. Sur une grande bibliothèque, "
    "compter quelques minutes — d'où le bouton « Charger le dernier audit ».",
    icon="⏱️",
)

base = Path(dossier)

if lancer:
    if not base.is_dir():
        st.error(f"Dossier introuvable : {base}")
        st.stop()
    with st.status("Audit en cours…", expanded=True) as status:
        suspects = fonds.auditer(base, seuil_suspect=seuil, log=lambda m: st.write(m))
        fonds.sauver_audit(suspects, base)
        status.update(label="Audit terminé ✅", state="complete")
    st.session_state["audit"] = suspects
elif charger:
    suspects = fonds.charger_audit(base)
    if suspects is None:
        st.warning("Aucun audit sauvegardé dans ce dossier.")
    else:
        st.session_state["audit"] = suspects

suspects = st.session_state.get("audit")
if not suspects:
    st.stop()

erreurs = [s for s in suspects if s.probable_erreur]
st.success(f"{len(suspects)} couple(s) à score faible — dont {len(erreurs)} erreur(s) probable(s).")

# Tableau récapitulatif
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

if st.button("💾 Générer le rapport HTML dans le dossier"):
    chemin = base / "audit_suspects.html"
    chemin.write_text(fonds.rapport_html(suspects, base), encoding="utf-8")
    st.success(f"Rapport écrit : `{chemin}`")

# Aperçu visuel : portrait · paysage actuel · paysage proposé
st.divider()
st.markdown("#### Aperçu visuel")
n_max = st.slider("Nombre de couples à afficher", 5, len(suspects), min(15, len(suspects)))

for s in suspects[:n_max]:
    badge = "⚠️ erreur probable" if s.probable_erreur else "score faible"
    st.markdown(f"**{s.ident}_po** — {badge}")
    c1, c2, c3 = st.columns(3)
    po = fonds.fichier_pour(base, s.ident, "po")
    pa = fonds.fichier_pour(base, s.ident, "pa")
    prop = fonds.fichier_pour(base, s.meilleur_ident, "pa")
    if po:
        c1.image(str(po), caption=f"portrait {s.ident}_po")
    if pa:
        c2.image(str(pa), caption=f"paysage actuel {s.ident}_pa (score {s.score_propre})")
    if prop:
        c3.image(str(prop), caption=f"proposé {s.meilleur_ident}_pa (score {s.meilleur_score})")
    st.divider()
