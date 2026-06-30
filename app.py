"""Boîte à outils — point d'entrée Streamlit.

Lancer avec :  uv run streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="Boîte à outils", page_icon="🧰", layout="wide")


def page(chemin, titre, icone):
    return st.Page(f"pages/{chemin}", title=titre, icon=icone)


navigation = st.navigation(
    {
        "": [st.Page("pages/accueil.py", title="Accueil", icon="🏠", default=True)],
        "🎵 Audio": [
            page("audio_normaliser.py", "Normaliser des FLAC", "🎚️"),
            page("audio_extraire.py", "Extraire l'audio d'une vidéo", "🎵"),
            page("audio_renommer.py", "Renommer depuis les tags", "🏷️"),
        ],
        "🖼️ Images": [
            page("images_redimensionner.py", "Redimensionner / compresser", "📐"),
            page("images_convertir.py", "Convertir de format", "🔄"),
            page("images_doublons.py", "Trouver les doublons", "👯"),
            page("images_renumeroter.py", "Renuméroter", "🔢"),
            page("fonds_ecran.py", "Apparier des fonds d'écran", "🖼️"),
        ],
        "🎬 Vidéo": [
            page("video_merge.py", "Fusionner", "🎬"),
            page("video_decouper.py", "Découper", "✂️"),
            page("video_compresser.py", "Compresser", "🗜️"),
        ],
        "📄 PDF": [
            page("pdf_extract.py", "Extraire des pages", "✂️"),
            page("pdf_fusionner.py", "Fusionner", "📚"),
            page("pdf_pages.py", "Supprimer / pivoter des pages", "🔧"),
            page("pdf_images.py", "Images ↔ PDF", "🖼️"),
        ],
        "📁 Fichiers": [
            page("files_clean.py", "Nettoyer les noms", "🧹"),
            page("files_remplacer.py", "Renommer en masse", "🔁"),
            page("files_doublons.py", "Fichiers en double", "🧬"),
            page("files_arborescence.py", "Arborescence → Excel", "🌳"),
        ],
        "🔤 Données": [
            page("data_convertir.py", "Convertir un tableau", "🔀"),
        ],
        "📚 Biblio": [
            page("biblio_cotes.py", "Trier des cotes", "📇"),
        ],
    }
)
navigation.run()
