from pathlib import Path

import streamlit as st

from tools import traduction
from ui import FILETYPES_TEXTE, champ_fichier

st.title("🌐 Traduire un texte")
st.caption(
    "Traduction **hors-ligne** (NLLB-200, sans PyTorch). Un seul modèle couvre "
    "200 langues ; l'anglais → français est le cas par défaut."
)

# --- Texte à traduire : saisie directe ou fichier .txt --------------------- #
source_saisie = st.radio("Source du texte", ["Saisir", "Fichier .txt"], horizontal=True)
if source_saisie == "Saisir":
    texte = st.text_area(
        "Texte à traduire", height=200, placeholder="Colle ou écris ton texte ici…"
    )
else:
    chemin = champ_fichier("Fichier texte", "trad_fichier", filetypes=FILETYPES_TEXTE)
    texte = ""
    if chemin:
        p = Path(chemin)
        if p.is_file():
            texte = p.read_text(encoding="utf-8", errors="replace")
            st.caption(f"{len(texte)} caractères chargés.")
        else:
            st.error(f"Fichier introuvable : {p}")

# --- Langues + matériel ---------------------------------------------------- #
langues = list(traduction.LANGUES)
col1, col2 = st.columns(2)
langue_source = col1.selectbox("De", langues, index=langues.index("Anglais"))
langue_cible = col2.selectbox("Vers", langues, index=langues.index("Français"))

if traduction.gpu_disponible():
    materiel = st.radio("Matériel", ["CPU", "GPU"], horizontal=True)
else:
    materiel = "CPU"

if langue_source == langue_cible:
    st.info("Choisis deux langues différentes.")

# --- Modèle : téléchargement au premier usage ------------------------------ #
if not traduction.modele_present():
    st.warning(
        "Le modèle de traduction (~600 Mo) n'est pas encore téléchargé. "
        "C'est un téléchargement unique, mis en cache hors du projet."
    )
    if st.button("⬇️ Télécharger le modèle", type="primary"):
        barre = st.progress(0.0, "Téléchargement…")
        traduction.telecharger_modele(
            lambda fraction, libelle: barre.progress(fraction, f"Téléchargement — {libelle}")
        )
        st.rerun()
    st.stop()

# --- Traduction ------------------------------------------------------------ #
pret = bool(texte.strip()) and langue_source != langue_cible
if st.button("🌐 Traduire", type="primary", disabled=not pret):
    with st.spinner("Traduction en cours…"):
        try:
            resultat = traduction.traduire(
                texte,
                source=traduction.LANGUES[langue_source],
                cible=traduction.LANGUES[langue_cible],
                gpu=(materiel == "GPU"),
            )
        except Exception as e:  # noqa: BLE001 — message affiché à l'utilisateur
            st.error(f"Échec de la traduction : {e}")
            st.stop()
    st.text_area("Traduction", value=resultat, height=200)
    st.download_button(
        "⬇️ Télécharger .txt", resultat, file_name="traduction.txt", mime="text/plain"
    )
