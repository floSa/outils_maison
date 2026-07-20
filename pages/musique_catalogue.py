import random
from pathlib import Path

import pandas as pd
import streamlit as st

from tools.catalogue import (
    COLONNES,
    DOSSIERS_ARTISTES_DEFAUT,
    RacineIndisponible,
    ecrire_excel,
    excel_octets,
    recap,
    scanner,
)
from ui import champ_dossier, champ_fichier_sortie

st.title("🎵 Catalogue de la bibliothèque")
st.caption(
    "Liste **tous les albums** de la bibliothèque musicale (NAS) dans un fichier Excel à "
    "deux colonnes `Artiste` / `Album`. Lecture seule : rien n'est modifié sur la source."
)

racine = champ_dossier(
    "Racine de la bibliothèque", "catalogue_racine", valeur_defaut="M:/musiques"
)

if not racine:
    st.stop()

base = Path(racine)
dossiers_artistes = DOSSIERS_ARTISTES_DEFAUT

if st.button("Valider", type="primary"):
    barre = st.progress(0.0, text="Parcours de la bibliothèque…")

    def _prog(fait, total):
        barre.progress(fait / total if total else 1.0, text=f"Artiste {fait}/{total}")

    try:
        cat = scanner(base, dossiers_artistes, progress=_prog)
        barre.empty()
        st.session_state["catalogue"] = cat
        st.session_state["catalogue_racine"] = str(base)
        # Échantillon fixé au moment du scan (stable jusqu'au prochain Valider).
        autres, categories = cat.blocs()
        st.session_state["catalogue_apercu"] = (
            random.sample(autres, min(5, len(autres))),
            random.sample(categories, min(5, len(categories))),
        )
    except RacineIndisponible as e:
        barre.empty()
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
st.caption(
    f"Échantillon au hasard pour vérifier la structure — le fichier Excel contient "
    f"les {cat.total_albums} lignes."
)
ech_autres, ech_categories = st.session_state.get("catalogue_apercu", ([], []))

st.markdown("**Quelques artistes de `__Autres`**")
if ech_autres:
    st.dataframe(
        pd.DataFrame(ech_autres, columns=list(COLONNES)),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("— aucun —")

st.markdown("**Quelques albums des autres catégories**")
if ech_categories:
    st.dataframe(
        pd.DataFrame(ech_categories, columns=list(COLONNES)),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.caption("— aucun —")

st.divider()
st.markdown("#### Export")

# Téléchargement direct : évite tout choix de destination, sans risque d'écrire
# sous la racine.
st.download_button(
    "⬇️ Télécharger le fichier Excel",
    data=excel_octets(cat),
    file_name="catalogue_albums.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
)

st.caption("Ou enregistrer dans un dossier précis :")
cible = champ_fichier_sortie(
    "Fichier Excel de destination",
    "catalogue_sortie",
    valeur_defaut=str(Path.home() / "Desktop" / "catalogue_albums.xlsx"),
    filetypes=[("Excel", "*.xlsx"), ("Tous les fichiers", "*.*")],
)
if cible and st.button("Enregistrer le fichier Excel"):
    try:
        ecrit = ecrire_excel(cat, cible, racine)
        st.success(f"Écrit : `{ecrit}`")
    except ValueError as e:
        st.error(str(e))
    except OSError as e:
        st.error(f"Écriture impossible : {e}")
