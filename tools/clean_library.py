"""Normaliser les noms d'une bibliothèque musicale ``Artiste\\Album\\Titres``.

Typiquement après un import dont les dossiers et fichiers portent des métadonnées
techniques parasites. L'outil travaille **exclusivement** sur les noms de dossiers
et de fichiers — il ne lit ni n'écrit aucun tag ID3/Vorbis.

Deux temps, à l'image du reste de la boîte à outils :

- ``previsualiser_nettoyage(racine)`` calcule ce qui sera modifié, sans rien écrire
  (c'est l'« audit »).
- ``appliquer(plan, racine)`` exécute et écrit un journal d'annulation.

Deux règles sont couvertes ici (la 3ᵉ, le regroupement des « singles », est
assurée par l'outil dédié :mod:`tools.musique`) :

Règle 1 — nom de dossier d'album
    Supprime, **en fin de nom** et de façon répétée jusqu'à stabilité, les suffixes
    techniques : ``(AAAA)`` (année 19xx/20xx), ``(Clean)``/``(Explicit)``,
    ``[UPC…]``, ``[AAAA]``, ``{…}``. Les parenthèses porteuses de sens
    (``(Deluxe)``, ``(Bande Originale du Film)``, ``(Four Tet Remix)``…) et les
    parenthèses internes (``Génération(s)``) sont **préservées**.

Règle 2 — nom de fichier audio
    ``01. Artiste - Titre.flac`` → ``01 - Titre.flac``. Le découpage artiste/titre
    se fait sur le **premier** ``" - "`` seulement, pour ne pas casser un titre tel
    que ``07. Clothilde - 102 - 103`` → ``07 - 102 - 103``. Un fichier déjà au
    format ``01 - Titre`` n'est pas reconnu (tiret, pas point) : l'outil est donc
    idempotent.

Invariants : aucune perte de fichier (uniquement des renommages), aucun écrasement
(collision → suffixe `` (2)``, `` (3)``…), dossiers ``.``/``_`` ignorés à tous les
niveaux.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from tools.files import Renommage

AUDIO_EXT = {".flac", ".mp3", ".m4a", ".wav", ".ogg", ".opus", ".aiff", ".wma", ".alac"}
NOM_JOURNAL_NETTOYAGE = ".nettoyage_undo.json"

# Caractères interdits par le système de fichiers → remplacés par « _ ».
_CARACTERES_INTERDITS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# Règle 1 : suffixes techniques, reconnus uniquement en fin de chaîne.
_SUFFIXES_ALBUM = [
    re.compile(r"\((?:19|20)\d{2}\)\s*$"),            # (2018)
    re.compile(r"\((?:clean|explicit)\)\s*$", re.I),  # (Clean) / (Explicit)
    re.compile(r"\[UPC[^\]]*\]\s*$", re.I),           # [UPC5060525433962]
    re.compile(r"\[(?:19|20)\d{2}\]\s*$"),            # [2018]
    re.compile(r"\{[^}]*\}\s*$"),                     # {WEB}
]

# Règle 2 : « <num>. <reste> » ou « <num>) <reste> » (mais pas « <num> - … »).
_PISTE = re.compile(r"^\s*(\d{1,3})\s*[.)]\s*(.+)$")


def _assainir(nom: str) -> str:
    """Remplace les caractères interdits par « _ » (noms produits uniquement)."""
    return _CARACTERES_INTERDITS.sub("_", nom)


def nettoyer_nom_album(nom: str) -> str:
    """Applique la règle 1 : retire les suffixes techniques de fin, jusqu'à stabilité."""
    resultat = nom.rstrip()
    change = True
    while change:
        change = False
        for motif in _SUFFIXES_ALBUM:
            nouveau = motif.sub("", resultat).rstrip()
            if nouveau != resultat:
                resultat, change = nouveau, True
    return resultat


def renommer_piste(stem: str) -> str | None:
    """Applique la règle 2 sur un nom de fichier **sans extension**.

    :return: le nouveau nom (sans extension), ou ``None`` si le fichier n'est pas
        au format « numéro. reste » (donc à ne pas toucher — idempotence).
    """
    m = _PISTE.match(stem)
    if not m:
        return None
    num, reste = m.group(1), m.group(2)
    # Couper sur le PREMIER « - » seulement : la gauche (artiste) est jetée.
    titre = reste.split(" - ", 1)[1] if " - " in reste else reste
    return f"{int(num):02d} - {titre.strip()}"


@dataclass
class PlanNettoyage:
    albums: list[Renommage] = field(default_factory=list)  # dossiers d'album (règle 1)
    pistes: list[Renommage] = field(default_factory=list)  # fichiers audio (règle 2)

    def __bool__(self) -> bool:
        return bool(self.albums or self.pistes)


def _sous_dossiers_visibles(chemin: Path) -> list[Path]:
    """Sous-dossiers directs, hors dossiers ``.``/``_`` (systèmes, outils, ``Singles``… non)."""
    return sorted(
        p
        for p in chemin.iterdir()
        if p.is_dir() and not p.name.startswith((".", "_"))
    )


def previsualiser_nettoyage(racine: str | Path) -> PlanNettoyage:
    """Calcule les renommages des règles 1 et 2 sans rien modifier (l'« audit »)."""
    base = Path(racine)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")

    plan = PlanNettoyage()
    for artiste in _sous_dossiers_visibles(base):
        for album in _sous_dossiers_visibles(artiste):
            # Règle 2 — récursive (albums multi-disques CD 01 / CD 02).
            for f in sorted(album.rglob("*")):
                if not f.is_file() or f.suffix.lower() not in AUDIO_EXT:
                    continue
                nouveau_stem = renommer_piste(f.stem)
                if nouveau_stem is None:
                    continue
                cible = f.with_name(_assainir(nouveau_stem) + f.suffix)
                if cible != f:
                    plan.pistes.append(Renommage(ancien=f, nouveau=cible))
            # Règle 1 — nom du dossier d'album.
            nouveau_nom = _assainir(nettoyer_nom_album(album.name))
            if nouveau_nom and nouveau_nom != album.name:
                plan.albums.append(
                    Renommage(ancien=album, nouveau=album.with_name(nouveau_nom))
                )
    return plan


def _libre(cible: Path, reserves: set[str]) -> Path:
    """Chemin cible non utilisé (ni sur disque, ni réservé) ; suffixe (2), (3)…"""
    if str(cible).lower() not in reserves and not cible.exists():
        reserves.add(str(cible).lower())
        return cible
    tige, ext = cible.stem, cible.suffix
    i = 2
    while True:
        candidat = cible.with_name(f"{tige} ({i}){ext}")
        if str(candidat).lower() not in reserves and not candidat.exists():
            reserves.add(str(candidat).lower())
            return candidat
        i += 1


def appliquer(plan: PlanNettoyage, racine: str | Path) -> Path:
    """Exécute le plan et écrit un journal d'annulation. Retourne le chemin du journal.

    Les fichiers sont renommés **avant** les dossiers d'album : ainsi le renommage
    d'un dossier déplace des fichiers déjà à leur nom final, et les chemins
    calculés restent valides.
    """
    reserves: set[str] = set()
    journal: list[dict[str, str]] = []
    for lot in (plan.pistes, plan.albums):
        for r in lot:
            if not r.ancien.exists():
                continue
            cible = _libre(r.nouveau, reserves)
            cible.parent.mkdir(parents=True, exist_ok=True)
            r.ancien.rename(cible)
            journal.append({"de": str(cible), "vers": str(r.ancien)})

    chemin = Path(racine) / NOM_JOURNAL_NETTOYAGE
    chemin.write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")
    return chemin


def annuler(racine: str | Path) -> int:
    """Restaure les noms d'origine depuis le journal. Retourne le nombre d'actions annulées.

    Parcours en ordre inverse : les dossiers d'album reviennent à leur nom avant
    les fichiers qu'ils contiennent.
    """
    chemin = Path(racine) / NOM_JOURNAL_NETTOYAGE
    if not chemin.is_file():
        raise FileNotFoundError(f"Aucun journal de nettoyage dans {racine}")

    entrees = json.loads(chemin.read_text(encoding="utf-8"))
    n = 0
    for e in reversed(entrees):
        de, vers = Path(e["de"]), Path(e["vers"])
        if de.exists() and not vers.exists():
            vers.parent.mkdir(parents=True, exist_ok=True)
            de.rename(vers)
            n += 1
    return n
