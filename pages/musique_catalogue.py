from pathlib import Path

import pandas as pd
import streamlit as st

from tools.catalogue import (
    DOSSIERS_ARTISTES_DEFAUT,
    RacineIndisponible,
    csv_texte,
    ecrire_csv,
    recap,
    scanner,
)
from ui import FILETYPES_CSV, champ_dossier, champ_fichier_sortie

st.title("🎵 Catalogue de la bibliothèque")
st.caption(
    "Liste **tous les albums** de la bibliothèque musicale (NAS) dans un CSV à deux "
    "colonnes `artiste_ou_categorie;album`. Lecture seule : rien n'est modifié sur la source."
)

racine = champ_dossier(
    "Racine de la bibliothèque", "catalogue_racine", valeur_defaut="M:/musiques"
)

if not racine:
    st.stop()

base = Path(racine)
dossiers_artistes = DOSSIERS_ARTISTES_DEFAUT

if st.button("Valider", type="primary"):
    with st.spinner("Parcours de la bibliothèque…"):
        try:
            st.session_state["catalogue"] = scanner(base, dossiers_artistes)
            st.session_state["catalogue_racine"] = str(base)
        except RacineIndisponible as e:
            st.session_state.pop("catalogue", None)
            st.error(str(e))

cat = st.session_state.get("catalogue")
if not cat:
    st.stop()

racine = st.session_state["catalogue_racine"]

st.markdown("#### Récapitulatif")
st.code(recap(cat, racine), language=None)

if cat.avertissements:
    with st.expander(f"⚠️ Avertissements ({len(cat.avertissements)})"):
        for a in cat.avertissements:
            st.write(f"- {a}")

st.markdown("#### Aperçu")
df = pd.DataFrame(cat.lignes, columns=["artiste_ou_categorie", "album"])
st.dataframe(df, use_container_width=True, hide_index=True, height=400)

st.divider()
st.markdown("#### Export")

# Téléchargement direct : évite tout choix de destination, sans risque d'écrire
# sous la racine. Le BOM utf-8-sig garantit les accents corrects dans Excel FR.
st.download_button(
    "⬇️ Télécharger le CSV",
    data=csv_texte(cat).encode("utf-8-sig"),
    file_name="catalogue_albums.csv",
    mime="text/csv",
    type="primary",
)

st.caption("Ou enregistrer dans un dossier précis :")
cible = champ_fichier_sortie(
    "Fichier CSV de destination",
    "catalogue_sortie",
    valeur_defaut=str(Path.home() / "Desktop" / "catalogue_albums.csv"),
    filetypes=FILETYPES_CSV,
)
if cible and st.button("Enregistrer le CSV"):
    try:
        ecrit = ecrire_csv(cat, cible, racine)
        st.success(f"Écrit : `{ecrit}`")
    except ValueError as e:
        st.error(str(e))
    except OSError as e:
        st.error(f"Écriture impossible : {e}")
