# 🧰 Boîte à outils

Petite application **Streamlit** regroupant des utilitaires locaux pour gérer
fichiers, médias et catalogues. Chaque outil est un onglet ; la logique métier
vit dans le package `tools/` (fonctions pures, testables), l'interface dans `pages/`.

## Installation

Projet géré avec [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync                    # dépendances de base
uv sync --extra vision     # + appariement de fonds d'écran (OpenCV seul, ~60 Mo)
```

## Lancer l'application

```bash
uv run streamlit run app.py
```

## Structure

```
app.py            # entrée Streamlit (navigation multipage)
tools/            # logique pure, sans Streamlit (testable)
  ffmpeg_utils.py #   accès au binaire ffmpeg embarqué
  audio.py        #   normalisation FLAC, extraction, renommage par tags
  images.py       #   redimensionner, convertir, dédupliquer, renuméroter
  video.py        #   fusionner, découper, compresser
  pdf.py          #   extraire, fusionner, pages, images ↔ PDF
  files.py        #   noms de fichiers, doublons, arborescence (+ annulation)
  data.py         #   conversions CSV / Excel / JSON
  biblio.py       #   tri de cotes de bibliothèque
  fonds.py        #   appariement fonds d'écran SIFT+RANSAC (extra vision)
pages/            # une page Streamlit par outil
tests/            # tests pytest (logique + rendu des pages)
notebooks_archive/# notebooks d'origine, conservés en référence
```

## Outils

| Catégorie | Outils |
|---|---|
| 🎵 Audio | Normaliser des FLAC · Convertir · Extraire l'audio d'une vidéo · Découper · Normaliser le volume · Renommer / éditer les tags · Regrouper les singles |
| 🖼️ Images | Redimensionner / compresser · Convertir (dont HEIC) · Doublons · Renuméroter · Apparier des fonds d'écran¹ · Auditer les fonds triés¹ |
| 🎬 Vidéo | Fusionner · Découper · Compresser · Convertir · Extraire des images · Créer un GIF |
| 📄 PDF | Extraire des pages · Fusionner · Supprimer / pivoter · Images ↔ PDF · Compresser · Protéger / déprotéger · Extraire le texte |
| 📁 Fichiers | Nettoyer les noms · Renommer en masse · Renommer depuis un CSV · Doublons · Ranger automatiquement · Statistiques · Comparer deux dossiers · Arborescence → Excel |
| 🔤 Données | Convertir CSV ↔ Excel ↔ JSON · Nettoyer des lignes |
| 📚 Biblio | Trier des cotes · Vérifier la disponibilité BM Lyon² |

> Les outils audio/vidéo utilisent le **ffmpeg embarqué** par `imageio-ffmpeg` (aucune
> installation système requise).
>
> ¹ L'appariement de fonds d'écran (paysage ↔ portrait, par SIFT + RANSAC) nécessite
> l'extra `vision` : `uv sync --extra vision`.
>
> ² La vérification BM Lyon nécessite l'extra `scraping` :
> `uv sync --extra scraping` puis `uv run playwright install chromium`.

## Tests

```bash
uv run pytest
```
