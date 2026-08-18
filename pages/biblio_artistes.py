import io
import threading
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from tools.biblio import extraire_colonne_artistes
from ui import champ_fichier

FILETYPES_ARTISTES = [
    ("CSV ou Excel", "*.csv *.xlsx *.xls"),
    ("Tous les fichiers", "*.*"),
]

st.title("🎧 Récupérer les CD d'artistes au catalogue BM Lyon")
st.caption(
    "À partir d'une colonne « Artiste » (CSV ou Excel), récolte tous les CD "
    "actuellement disponibles à la Part-Dieu, avec leur cote. Une cellule "
    "avec plusieurs artistes séparés par une virgule est recherchée nom par "
    "nom, puis les résultats sont fusionnés par disque."
)
st.caption(
    "« Score confiance » : similarité entre le nom recherché (colonne "
    "« Artiste ») et l'auteur tel qu'écrit sur la fiche (« Artiste trouvé »), "
    "de 0 à 1. Un disque est retenu à partir de 0.85, ou en-dessous si le nom "
    "recherché est inclus dans le nom trouvé (ex. « Bourvil » dans "
    "« André Bourvil »)."
)
st.caption(
    "Journal pendant la récolte : 🔍 recherche en cours · 🔁 artiste déjà "
    "recherché (résultat réutilisé, pas de nouvelle requête) · ✅ disque "
    "retenu avec sa cote · ❌ aucun CD trouvé pour ce nom · 💥 erreur réseau."
)

# --- Dépendance navigateur (Playwright) ---------------------------------------
try:
    import playwright  # noqa: F401

    from tools.bm_lyon import normalize, recolter_disques_artistes
except ModuleNotFoundError:
    st.warning(
        "Cet outil nécessite Playwright et son navigateur :\n\n"
        "```\nuv sync\nuv run playwright install chromium\n```",
        icon="📦",
    )
    st.stop()

chemin = champ_fichier(
    "Fichier CSV ou Excel (colonne « Artiste »)",
    "bm_artistes_chemin",
    filetypes=FILETYPES_ARTISTES,
    placeholder="C:/Users/.../artistes.xlsx",
)

groupes: list[str] = []
if chemin and Path(chemin).is_file():
    try:
        suffixe = Path(chemin).suffix.lower()
        tableau = pd.read_excel(chemin) if suffixe in (".xlsx", ".xls") else pd.read_csv(chemin)
        groupes = extraire_colonne_artistes(tableau)
    except ValueError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Impossible de lire le fichier : {exc}")
elif chemin:
    st.error("Fichier introuvable.")

if groupes:
    n_uniques = len({normalize(g) for g in groupes if normalize(g)})
    if n_uniques < len(groupes):
        st.write(
            f"{len(groupes)} ligne(s) dans le fichier, **{n_uniques} artiste(s) unique(s)** "
            f"à rechercher (doublons dédupliqués automatiquement — même artiste sur "
            f"plusieurs lignes, ex. une ligne par album déjà connu)."
        )
    else:
        st.write(f"{len(groupes)} groupe(s) d'artiste(s) à rechercher.")

def _lancer_recolte(groupes, journal, avancement, sortie, arret):
    """Tourne dans un thread séparé : ne doit appeler AUCUNE fonction Streamlit
    (interdit hors du thread principal), seulement muter des objets Python
    simples (liste/dict) que la page relit à chaque rafraîchissement."""
    try:
        resultats = recolter_disques_artistes(
            groupes,
            log=journal.append,
            progress=lambda i, total: avancement.update(i=i, total=total),
            arret=arret,
        )
        sortie["resultats"] = resultats
    except Exception as exc:
        sortie["erreur"] = str(exc)


en_cours = st.session_state.get("bm_artistes_en_cours", False)
valider = st.button("Récolter", type="primary", disabled=not groupes or en_cours)

if valider and not en_cours:
    st.session_state["bm_artistes_journal"] = []
    st.session_state["bm_artistes_avancement"] = {"i": 0, "total": 1}
    st.session_state["bm_artistes_sortie"] = {}
    st.session_state["bm_artistes_arret"] = threading.Event()
    st.session_state["bm_artistes_confirmer_arret"] = False
    st.session_state.pop("bm_artistes_erreur", None)
    thread = threading.Thread(
        target=_lancer_recolte,
        args=(
            groupes,
            st.session_state["bm_artistes_journal"],
            st.session_state["bm_artistes_avancement"],
            st.session_state["bm_artistes_sortie"],
            st.session_state["bm_artistes_arret"],
        ),
        daemon=True,
    )
    st.session_state["bm_artistes_thread"] = thread
    st.session_state["bm_artistes_en_cours"] = True
    thread.start()
    st.rerun()

if st.session_state.get("bm_artistes_en_cours"):
    thread = st.session_state["bm_artistes_thread"]
    avancement = st.session_state["bm_artistes_avancement"]
    journal = st.session_state["bm_artistes_journal"]

    barre = st.progress(
        avancement["i"] / avancement["total"],
        text=f"Recherche {avancement['i']}/{avancement['total']}",
    )
    with st.container(height=250):
        st.code("\n".join(journal) or "Démarrage du navigateur…", language=None)

    if thread.is_alive():
        if not st.session_state.get("bm_artistes_confirmer_arret"):
            if st.button("⏹ Arrêter la récolte"):
                st.session_state["bm_artistes_confirmer_arret"] = True
                st.rerun()
        else:
            st.warning(
                "Arrêter la récolte en cours ? Les disques déjà trouvés jusqu'ici "
                "seront conservés."
            )
            col_oui, col_non = st.columns(2)
            if col_oui.button("Oui, arrêter", type="primary"):
                st.session_state["bm_artistes_arret"].set()
                st.session_state["bm_artistes_confirmer_arret"] = False
                st.rerun()
            if col_non.button("Annuler"):
                st.session_state["bm_artistes_confirmer_arret"] = False
                st.rerun()
        time.sleep(1)
        st.rerun()
    else:
        sortie = st.session_state["bm_artistes_sortie"]
        st.session_state["bm_artistes_en_cours"] = False
        if "erreur" in sortie:
            st.session_state["bm_artistes_erreur"] = sortie["erreur"]
        else:
            st.session_state["bm_artistes_resultats"] = sortie.get("resultats", [])
        st.rerun()

if st.session_state.get("bm_artistes_erreur"):
    st.error(f"Erreur : {st.session_state['bm_artistes_erreur']}")

resultats = st.session_state.get("bm_artistes_resultats")
if resultats:
    df_resultats = pd.DataFrame(
        [
            {
                "Artiste": r.artiste_recherche,
                "Album": r.album,
                "Cote": r.cote,
                "Statut": r.statut,
                "Artiste trouvé": r.artiste_trouve,
                "Score confiance": r.score_artiste,
            }
            for r in resultats
        ]
    )
    st.success(f"{len(resultats)} disque(s) trouvé(s) à la Part-Dieu.")
    st.dataframe(df_resultats, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    col1.download_button(
        "⬇️ Export CSV",
        df_resultats.to_csv(index=False).encode("utf-8-sig"),
        file_name="cd_artistes_bm_lyon.csv",
        mime="text/csv",
    )
    tampon = io.BytesIO()
    df_resultats.to_excel(tampon, index=False)
    col2.download_button(
        "⬇️ Export Excel",
        tampon.getvalue(),
        file_name="cd_artistes_bm_lyon.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
