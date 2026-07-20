from pathlib import Path

import streamlit as st

from tools.biblio import formater, parser_lignes, trier_par_cote
from ui import FILETYPES_TEXTE, champ_fichier

st.title("📇 Trier des cotes de bibliothèque")
st.caption("Trie des entrées « Artiste - Album - Cote » par cote (type Dewey musique).")

col_source, col_btn = st.columns([4, 1], vertical_alignment="bottom")
source = col_source.radio("Source", ["Coller du texte", "Fichier"], horizontal=True)

texte = ""
chemin = ""
if source == "Coller du texte":
    texte = st.text_area(
        "Lignes à trier",
        height=200,
        placeholder="Cliff Martinez - The Knick - 786.1 KNI 3\nDanny Elfman - Alice - 786 B.O",
    )
else:
    chemin = champ_fichier(
        "Fichier texte",
        "biblio_cotes_chemin",
        filetypes=FILETYPES_TEXTE,
        placeholder="C:/Users/.../cotes_bibli.txt",
    )
    if chemin and Path(chemin).is_file():
        texte = Path(chemin).read_text(encoding="utf-8")
    elif chemin:
        st.error("Fichier introuvable.")

# Bouton d'action, sur la même ligne que « Source ».
valider = col_btn.button("Valider", type="primary", use_container_width=True)

if valider:
    entrees = parser_lignes(texte)
    if not entrees:
        st.session_state.pop("cotes_resultat", None)
        st.error(
            "Rien à trier : colle des lignes « Artiste - Album - Cote » "
            "(une par ligne) ou choisis un fichier."
        )
    else:
        st.session_state["cotes_resultat"] = formater(trier_par_cote(entrees))
        st.session_state["cotes_sans_cote"] = [e.brut for e in entrees if not e.cote]

resultat = st.session_state.get("cotes_resultat")
if not resultat:
    st.stop()

for brut in st.session_state.get("cotes_sans_cote", []):
    st.warning(f"Ligne sans cote reconnue (placée en fin) : `{brut}`")

st.markdown("#### Résultat trié")
st.code(resultat, language="text")
st.download_button("Télécharger", resultat, file_name="cotes_triees.txt")

if source == "Fichier" and chemin and st.button("Écraser le fichier source avec le tri"):
    Path(chemin).write_text(resultat + "\n", encoding="utf-8")
    st.success("Fichier mis à jour.")
