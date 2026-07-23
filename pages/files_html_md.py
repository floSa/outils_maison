from pathlib import Path

import pandas as pd
import streamlit as st

from tools.html_md import convertir, lister_sources
from ui import champ_dossier, champ_mixte

st.title("🌐 HTML → Markdown")
st.caption(
    "Nettoie des captures web faites avec l'extension **SingleFile** et les "
    "convertit en Markdown propre (interface, pubs et scripts retirés)."
)

entree = champ_mixte(
    "Fichier .html ou dossier à convertir",
    "html_md_entree",
    aide="Un fichier .html unique, ou un dossier (tous les .html sont traités récursivement).",
)
sortie = champ_dossier(
    "Dossier de sortie",
    "html_md_sortie",
    aide="Les .md (et leurs dossiers d'images _assets/) y sont créés, arborescence conservée.",
)

if not entree or not sortie:
    st.stop()

src = Path(entree)
if not src.exists():
    st.error(f"Introuvable : {src}")
    st.stop()

sources = lister_sources(src)
if not sources:
    st.warning("Aucun fichier .html trouvé.")
    st.stop()
st.caption(f"{len(sources)} fichier(s) .html à traiter.")

if st.button("Convertir", type="primary"):
    with st.spinner("Conversion…"):
        resultats = convertir(src, Path(sortie))

    n_review = sum(r.status == "review" for r in resultats)
    n_erreurs = sum(r.status == "error" for r in resultats)
    n_ok = len(resultats) - n_review - n_erreurs
    resume = f"{len(resultats)} fichier(s) — {n_ok} ok, {n_review} à vérifier, {n_erreurs} en erreur."
    if n_erreurs:
        st.error(resume)
    elif n_review:
        st.warning(resume)
    else:
        st.success(resume)

    icones = {"ok": "✅", "review": "⚠️", "error": "❌"}
    df = pd.DataFrame(
        [
            {
                "": icones[r.status],
                "Source": r.source.name,
                "Sortie": r.output.name if r.output else "—",
                "Stratégie": r.strategy,
                "Caractères": r.chars_out,
                "Images": r.images,
                "Détail": r.detail,
            }
            for r in resultats
        ]
    )
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(
        "« À vérifier » = le nettoyage a peut-être vidé la page (ratio de texte "
        "faible ou sortie très courte) — ouvre le .md pour contrôler."
    )
