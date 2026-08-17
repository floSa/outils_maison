import io
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

# --- Dépendance navigateur (Playwright) ---------------------------------------
try:
    import playwright  # noqa: F401

    from tools.bm_lyon import recolter_disques_artistes
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
    st.write(f"{len(groupes)} groupe(s) d'artiste(s) à rechercher.")

valider = st.button("Récolter", type="primary", disabled=not groupes)

if valider:
    barre = st.progress(0.0, text="Démarrage du navigateur…")
    journal = st.status("Recherche au catalogue…", expanded=True)

    def _progress(i, total):
        barre.progress(i / total, text=f"Groupe {i}/{total}")

    with journal as statut:
        try:
            resultats = recolter_disques_artistes(
                groupes,
                log=lambda m: st.write(m),
                progress=_progress,
            )
            statut.update(label="Récolte terminée ✅", state="complete")
        except Exception as exc:
            statut.update(label="Échec ❌", state="error")
            st.error(f"Erreur : {exc}")
            st.stop()

    st.session_state["bm_artistes_resultats"] = resultats
    barre.progress(1.0, text="Terminé")

resultats = st.session_state.get("bm_artistes_resultats")
if resultats:
    df_resultats = pd.DataFrame(
        [
            {
                "Artiste(s) recherché(s)": r.artistes_recherches,
                "Artiste trouvé": r.artiste_trouve,
                "Album": r.album,
                "Cotes (Part-Dieu)": ", ".join(r.cotes),
                "Statuts": ", ".join(r.statuts),
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
