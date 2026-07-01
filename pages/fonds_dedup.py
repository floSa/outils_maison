from pathlib import Path

import streamlit as st

from tools import fonds

st.title("🧹 Dédupliquer les fonds triés")
st.caption(
    "Garde un couple propre par visuel, isole les copies redondantes dans `Doublons/` "
    "et les images uniques sans partenaire dans `A_verifier/`. Rien n'est supprimé."
)

DEFAUT = "C:/Users/FLORIAN/Pictures/FDE/Fonds_Tries"
dossier = st.text_input("Dossier trié", value=DEFAUT)
base = Path(dossier)

suspects_data = fonds.charger_audit(base) if base.is_dir() else None
if suspects_data is None:
    st.warning(
        "Aucun audit trouvé dans ce dossier. Lance d'abord **Auditer les fonds triés** "
        "(le résultat sert à repérer les couples cassés).",
        icon="ℹ️",
    )
    st.stop()

suspects = {s.ident for s in suspects_data}
st.info(f"{len(suspects)} couple(s) suspect(s) chargé(s) depuis le dernier audit.")

confirmes = st.text_input(
    "Numéros à considérer corrects malgré un score faible (séparés par des virgules)",
    value="119, 266, 819, 908",
    help="Ces couples seront conservés au lieu d'être isolés.",
)
seuil = st.slider("Tolérance doublon (empreinte perceptuelle)", 0, 10, 4)

confirmes_ok = {c.strip() for c in confirmes.split(",") if c.strip()}

if st.button("Calculer le plan", type="primary"):
    with st.spinner("Analyse des empreintes…"):
        plan = fonds.plan_deduplication(
            base, suspects=suspects, confirmes_ok=confirmes_ok, seuil_hash=seuil
        )
    st.session_state["dedup_plan"] = plan

plan = st.session_state.get("dedup_plan")
if plan:
    c1, c2, c3 = st.columns(3)
    c1.metric("Couples gardés", len(plan.gardes))
    c2.metric("→ Doublons/", len(plan.doublons))
    c3.metric("→ A_verifier/", len(plan.a_verifier))

    with st.expander(f"A_verifier ({len(plan.a_verifier)} images uniques à revoir)"):
        st.write(", ".join(sorted(f.name for f in plan.a_verifier)) or "(aucune)")

    st.warning("Déplace les fichiers (réversible). Rien n'est supprimé.", icon="⚠️")
    if st.button(f"Appliquer ({len(plan.doublons) + len(plan.a_verifier)} fichiers déplacés)"):
        journal = fonds.appliquer_deduplication(plan, base)
        st.success(f"Terminé. Journal : `{journal.name}`")
        st.session_state.pop("dedup_plan", None)

if base.is_dir() and (base / ".dedup_undo.json").is_file():
    st.divider()
    if st.button("↩️ Annuler la dernière déduplication"):
        n = fonds.annuler_deduplication(base)
        st.success(f"{n} fichier(s) restauré(s).")
