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
| 🎵 Audio | Normaliser des FLAC · Extraire l'audio d'une vidéo · Renommer depuis les tags · Regrouper les singles |
| 🖼️ Images | Redimensionner / compresser · Convertir (dont HEIC) · Doublons · Renuméroter · Apparier des fonds d'écran¹ |
| 🎬 Vidéo | Fusionner · Découper · Compresser |
| 📄 PDF | Extraire des pages · Fusionner · Supprimer / pivoter · Images ↔ PDF |
| 📁 Fichiers | Nettoyer les noms · Renommer en masse · Doublons · Arborescence → Excel |
| 🔤 Données | Convertir CSV ↔ Excel ↔ JSON |
| 📚 Biblio | Trier des cotes |

> Les outils audio/vidéo utilisent le **ffmpeg embarqué** par `imageio-ffmpeg` (aucune
> installation système requise).
>
> ¹ L'appariement de fonds d'écran (paysage ↔ portrait, par SIFT + RANSAC) nécessite
> l'extra `vision` : `uv sync --extra vision`.

## Tests

```bash
uv run pytest
```
