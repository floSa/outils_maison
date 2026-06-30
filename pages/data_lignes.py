from pathlib import Path

import streamlit as st

from tools.data import traiter_lignes

st.title("📃 Nettoyer des lignes de texte")
st.caption("Déduplique, trie et retire les lignes vides d'un texte ou d'un fichier.")

source = st.radio("Source", ["Coller du texte", "Fichier"], horizontal=True)
texte = ""
chemin = None
if source == "Coller du texte":
    texte = st.text_area("Lignes", height=200, placeholder="une ligne\nune autre\nune ligne")
else:
    chemin = st.text_input("Fichier texte", placeholder="C:/Users/.../liste.txt")
    if chemin and Path(chemin).is_file():
        texte = Path(chemin).read_text(encoding="utf-8")
    elif chemin:
        st.error("Fichier introuvable.")

col1, col2, col3 = st.columns(3)
dedup = col1.checkbox("Dédupliquer", value=True)
trier = col2.checkbox("Trier", value=False)
ignorer_casse = col3.checkbox("Ignorer la casse", value=False)

if not texte.strip():
    st.stop()

lignes, retirees = traiter_lignes(
    texte, dedupliquer=dedup, trier=trier, ignorer_casse=ignorer_casse
)
resultat = "\n".join(lignes)

st.success(f"{len(lignes)} ligne(s) — {retirees} retirée(s).")
st.code(resultat or "(vide)", language="text")
st.download_button("Télécharger", resultat + "\n", file_name="lignes.txt")

if source == "Fichier" and chemin and st.button("Écraser le fichier source"):
    Path(chemin).write_text(resultat + "\n", encoding="utf-8")
    st.success("Fichier mis à jour.")
