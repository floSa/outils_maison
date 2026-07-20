from pathlib import Path

import streamlit as st

from tools.biblio import formater, parser_lignes, trier_par_cote
from ui import FILETYPES_TEXTE, champ_fichier

st.title("📇 Trier des cotes de bibliothèque")
st.caption("Trie des entrées « Artiste - Album - Cote » par cote (type Dewey musique).")

source = st.radio("Source", ["Coller du texte", "Fichier"], horizontal=True)

texte = ""
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

if not texte.strip():
    st.stop()

if st.button("Trier", type="primary"):
    st.session_state["cotes_resultat"] = formater(trier_par_cote(parser_lignes(texte)))

resultat = st.session_state.get("cotes_resultat")
if not resultat:
    st.stop()

st.markdown("#### Résultat trié")
st.code(resultat, language="text")
st.download_button("Télécharger", resultat, file_name="cotes_triees.txt")

if source == "Fichier" and st.button("Écraser le fichier source avec le tri"):
    Path(chemin).write_text(resultat + "\n", encoding="utf-8")
    st.success("Fichier mis à jour.")
