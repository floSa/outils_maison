import io
from pathlib import Path

import pandas as pd
import streamlit as st

from tools.biblio import parser_lignes
from ui import FILETYPES_TEXTE, champ_fichier

st.title("📗 Vérifier la disponibilité BM Lyon")
st.caption(
    "Re-vérifie le statut ACTUEL (En rayon / Prêté…) de cotes déjà connues au "
    "catalogue de la bibliothèque municipale de Lyon (Part-Dieu)."
)

# --- Dépendance navigateur (Playwright) ---------------------------------------
try:
    import playwright  # noqa: F401

    from tools.bm_lyon import verifier_disponibilites
except ModuleNotFoundError:
    st.warning(
        "Cet outil nécessite Playwright et son navigateur :\n\n"
        "```\nuv sync\nuv run playwright install chromium\n```",
        icon="📦",
    )
    st.stop()

col_source, col_btn = st.columns([4, 1], vertical_alignment="bottom")
source = col_source.radio("Source", ["Coller du texte", "Fichier"], horizontal=True)

texte = ""
if source == "Coller du texte":
    texte = st.text_area(
        "Lignes « Artiste - Album - Cote » (une par ligne, copiées depuis un tableur)",
        height=220,
        placeholder="Cliff Martinez - The Knick - 786.1 KNI 3\nGaëtan Roussel - Ginger - 780.65 ROU",
    )
else:
    chemin = champ_fichier(
        "Fichier texte",
        "bm_dispo_chemin",
        filetypes=FILETYPES_TEXTE,
        placeholder="C:/Users/.../cotes_bibli.txt",
    )
    if chemin and Path(chemin).is_file():
        texte = Path(chemin).read_text(encoding="utf-8")
    elif chemin:
        st.error("Fichier introuvable.")

entrees = [e for e in parser_lignes(texte) if e.cote] if texte.strip() else []
invalides = [e for e in parser_lignes(texte) if not e.cote] if texte.strip() else []

# Bouton d'action, sur la même ligne que « Source ».
valider = col_btn.button("Vérifier", type="primary", use_container_width=True)

if texte.strip():
    st.write(f"{len(entrees)} ligne(s) exploitable(s).")
    for e in invalides:
        st.warning(f"Ligne sans cote reconnue (ignorée) : `{e.brut}`")

if valider:
    if not entrees:
        st.session_state.pop("bm_resultats", None)
        st.error(
            "Aucune cote exploitable : colle des lignes « Artiste - Album - Cote » "
            "ou choisis un fichier."
        )
    else:
        barre = st.progress(0.0, text="Démarrage du navigateur…")
        journal = st.status("Vérification au catalogue…", expanded=True)

        def _progress(i, total):
            barre.progress(i / total, text=f"Ligne {i}/{total}")

        with journal as statut:
            try:
                resultats = verifier_disponibilites(
                    [(e.artiste, e.album, e.cote) for e in entrees],
                    log=lambda m: st.write(m),
                    progress=_progress,
                )
                statut.update(label="Vérification terminée ✅", state="complete")
            except Exception as exc:
                statut.update(label="Échec ❌", state="error")
                st.error(f"Erreur : {exc}")
                st.stop()

        st.session_state["bm_resultats"] = resultats
        barre.progress(1.0, text="Terminé")

resultats = st.session_state.get("bm_resultats")
if resultats:
    df = pd.DataFrame(
        [
            {
                "Artiste": r.artiste,
                "Album": r.album,
                "Cote": r.cote,
                "Statut actuel": r.statut_actuel,
                "Statut": r.statut,
                "Album trouvé": r.album_trouve,
                "Cotes sur la fiche": ", ".join(r.cotes_trouvees),
            }
            for r in resultats
        ]
    )
    ok = sum(r.statut == "OK trouvé" for r in resultats)
    st.success(f"{ok}/{len(resultats)} cote(s) confirmée(s).")
    st.dataframe(df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    col1.download_button(
        "⬇️ Export CSV",
        df.to_csv(index=False).encode("utf-8-sig"),
        file_name="disponibilites_bm_lyon.csv",
        mime="text/csv",
    )
    tampon = io.BytesIO()
    df.to_excel(tampon, index=False)
    col2.download_button(
        "⬇️ Export Excel",
        tampon.getvalue(),
        file_name="disponibilites_bm_lyon.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
