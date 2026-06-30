import streamlit as st

st.title("🧰 Boîte à outils")
st.caption("Petits utilitaires locaux pour gérer fichiers, médias et catalogues.")

st.markdown(
    """
Sélectionne un outil dans la barre latérale. Tous travaillent **sur tes dossiers locaux**.

| Catégorie | Outils |
|---|---|
| 🎵 **Audio** | Normaliser des FLAC · Extraire l'audio d'une vidéo · Renommer depuis les tags |
| 🖼️ **Images** | Redimensionner / compresser · Convertir (dont HEIC) · Trouver les doublons · Renuméroter |
| 🎬 **Vidéo** | Fusionner · Découper · Compresser |
| 📄 **PDF** | Extraire des pages · Fusionner · Supprimer / pivoter · Images ↔ PDF |
| 📁 **Fichiers** | Nettoyer les noms · Renommer en masse · Doublons · Arborescence → Excel |
| 🔤 **Données** | Convertir CSV ↔ Excel ↔ JSON |
| 📚 **Biblio** | Trier des cotes |
"""
)

st.info(
    "Les chemins se saisissent en collant le chemin complet du dossier ou du fichier "
    "(ex. `M:/musiques` ou `C:/Users/.../doc.pdf`).",
    icon="💡",
)

with st.expander("Outils nécessitant l'extra « vision » (non installé par défaut)"):
    st.markdown(
        "L'appariement de fonds d'écran (SIFT/CNN) requiert `torch` + `opencv` "
        "(~2-3 Go). Installer avec `uv sync --extra vision`."
    )
