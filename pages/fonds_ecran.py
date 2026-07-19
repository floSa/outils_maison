from pathlib import Path

import streamlit as st

st.title("🖼️ Apparier des fonds d'écran (paysage ↔ portrait)")
st.caption(
    "Le portrait est un recadrage zoomé du paysage. Appariement par SIFT + RANSAC "
    "(géométrique), du plus sûr au moins sûr."
)

# --- Dépendance optionnelle (extra « vision ») -------------------------------
try:
    import cv2  # noqa: F401

    from tools import fonds
except ModuleNotFoundError:
    st.warning(
        "Cet outil nécessite l'extra **vision** (OpenCV). "
        "Installe-le puis relance l'app :\n\n```\nuv sync --extra vision\n```",
        icon="📦",
    )
    st.stop()

from ui import champ_dossier

DEFAUT_SRC = "C:/Users/FLORIAN/Pictures/FDE"
DEFAUT_TRIES = "C:/Users/FLORIAN/Pictures/FDE/Fonds_Tries"

source = champ_dossier(
    "Dossier source (images en vrac)", "fonds_ecran_source", valeur_defaut=DEFAUT_SRC
)
dossier_tries = champ_dossier(
    "Dossier trié (destination)", "fonds_ecran_dossier_tries", valeur_defaut=DEFAUT_TRIES
)
col1, col2 = st.columns(2)
seuil = col1.slider("Seuil d'inliers minimum", 10, 100, fonds.SEUIL_INLIERS)
verifier_dup = col2.checkbox("Vérifier les couples déjà triés", value=True)

if st.button("Analyser", type="primary"):
    base = Path(source)
    if not base.is_dir():
        st.error(f"Dossier introuvable : {base}")
        st.stop()
    with st.status("Analyse SIFT…", expanded=True) as status:
        res = fonds.apparier(base, seuil=seuil, log=lambda m: st.write(m))
        empreintes = (
            fonds.empreintes_paysages(dossier_tries) if verifier_dup else []
        )
        status.update(label="Analyse terminée ✅", state="complete")

    # Marque les doublons déjà présents dans le dossier trié.
    deja = {}
    for c in res.couples:
        ident = fonds.couple_deja_trie(c.paysage, empreintes) if empreintes else None
        if ident:
            deja[c.portrait.name] = ident

    st.session_state["fonds_res"] = res
    st.session_state["fonds_deja"] = deja

res = st.session_state.get("fonds_res")
if not res:
    st.stop()

deja = st.session_state.get("fonds_deja", {})
st.success(
    f"{len(res.couples)} couple(s) — "
    f"{sum(c.certain for c in res.couples)} sûr(s), "
    f"{len(deja)} déjà trié(s), "
    f"{len(res.paysages_seuls)} paysage(s) et {len(res.portraits_seuls)} portrait(s) orphelins."
)

st.markdown("#### Couples proposés")
st.caption("Décoche ceux à ne pas ranger. Les doublons et incertains sont décochés par défaut.")

choisis = []
for c in res.couples:
    ident_dup = deja.get(c.portrait.name)
    badge = "✅ sûr" if c.certain else "⚠️ à vérifier"
    if ident_dup:
        badge += f" · 🔁 déjà trié ({ident_dup})"

    cocher, img_pa, img_po, info = st.columns([1, 3, 2, 3])
    defaut = c.certain and not ident_dup
    inclus = cocher.checkbox("Ranger", value=defaut, key=f"c_{c.portrait.name}", label_visibility="collapsed")
    img_pa.image(str(c.paysage), use_container_width=True)
    img_po.image(str(c.portrait), use_container_width=True)
    info.write(f"**{badge}**")
    info.write(f"score : **{c.score}** (2ᵉ : {c.second})")
    info.caption(f"{c.paysage.name[:18]}…\n{c.portrait.name[:18]}…")
    if inclus:
        choisis.append(c)

st.divider()
st.markdown("#### Ranger")
mode = st.radio(
    "Action sur les fichiers source",
    ["Déplacer (retirer de la source)", "Copier (conserver la source)"],
    horizontal=True,
)
st.caption(f"{len(choisis)} couple(s) coché(s) seront rangés en `NNN_pa`/`NNN_po`.")

if st.button(f"Ranger {len(choisis)} couple(s)", type="primary", disabled=not choisis):
    deplacer = mode.startswith("Déplacer")
    faits = fonds.ranger(choisis, dossier_tries, deplacer=deplacer)
    st.success(f"{len(faits)} couple(s) rangé(s) (ids {faits[0][0]} → {faits[-1][0]}).")
    # Réinitialise pour forcer une nouvelle analyse (les fichiers ont bougé).
    st.session_state.pop("fonds_res", None)
    st.session_state.pop("fonds_deja", None)
