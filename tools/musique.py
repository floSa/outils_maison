"""Regrouper les « singles » d'une bibliothèque musicale.

Arborescence attendue : racine / <artiste> / <album> / fichiers.
Un dossier album qui ne contient **qu'un seul fichier audio** (et éventuellement
une pochette) est un « single ». L'outil déplace ce titre dans <artiste>/Singles/,
renomme la pochette en ``cover_<nom du titre>``, puis supprime le dossier album vidé.

Sécurité : aperçu avant action, journal d'annulation, et tout dossier au contenu
inattendu (autre fichier, plusieurs images, sous-dossier) est signalé et laissé tel quel.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

EXT_AUDIO = (".flac", ".mp3", ".m4a", ".wav", ".ogg", ".opus", ".wma", ".aac", ".aiff", ".alac")
EXT_IMAGE = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff")
FICHIERS_JUNK = {"thumbs.db", ".ds_store", "desktop.ini"}
NOM_DOSSIER_SINGLES = "Singles"
NOM_JOURNAL = ".singles_undo.json"


@dataclass
class AlbumSingle:
    artiste: Path
    album: Path
    audio: Path
    cover: Path | None
    junk: list[Path] = field(default_factory=list)
    autres: list[Path] = field(default_factory=list)  # contenu inattendu (non vide → à vérifier)

    @property
    def a_verifier(self) -> bool:
        return bool(self.autres)


@dataclass
class Plan:
    a_traiter: list[AlbumSingle]
    a_verifier: list[AlbumSingle]


def _classer(album: Path) -> AlbumSingle | None:
    """Analyse un dossier album. Retourne un AlbumSingle si exactement 1 audio, sinon None."""
    audios, images, junk, autres, sous_dossiers = [], [], [], [], []
    for f in album.iterdir():
        if f.is_dir():
            sous_dossiers.append(f)
        elif f.name.lower() in FICHIERS_JUNK:
            junk.append(f)
        elif f.suffix.lower() in EXT_AUDIO:
            audios.append(f)
        elif f.suffix.lower() in EXT_IMAGE:
            images.append(f)
        else:
            autres.append(f)

    if len(audios) != 1:
        return None  # pas un single (vrai album, ou dossier vide)

    # Contenu inattendu → signalé (à vérifier), pas traité automatiquement.
    extra = list(autres) + [d for d in sous_dossiers]
    if len(images) > 1:
        extra += images
        cover = None
    else:
        cover = images[0] if images else None

    return AlbumSingle(
        artiste=album.parent,
        album=album,
        audio=audios[0],
        cover=cover,
        junk=junk,
        autres=extra,
    )


def analyser(racine: str | Path) -> Plan:
    """Parcourt racine/<artiste>/<album> et classe les dossiers single.

    :return: Plan(a_traiter, a_verifier).
    """
    base = Path(racine)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")

    a_traiter: list[AlbumSingle] = []
    a_verifier: list[AlbumSingle] = []
    for artiste in sorted(p for p in base.iterdir() if p.is_dir()):
        for album in sorted(p for p in artiste.iterdir() if p.is_dir()):
            if album.name.lower() == NOM_DOSSIER_SINGLES.lower():
                continue  # ne pas retraiter un dossier Singles existant
            sa = _classer(album)
            if sa is None:
                continue
            (a_verifier if sa.a_verifier else a_traiter).append(sa)
    return Plan(a_traiter=a_traiter, a_verifier=a_verifier)


def _nom_libre(dossier: Path, nom: str, reserves: set[str]) -> Path:
    """Chemin cible non utilisé (ni sur disque, ni déjà réservé) ; suffixe (2), (3)…"""
    cible = dossier / nom
    if str(cible).lower() not in reserves and not cible.exists():
        reserves.add(str(cible).lower())
        return cible
    tige, ext = cible.stem, cible.suffix
    i = 2
    while True:
        cible = dossier / f"{tige} ({i}){ext}"
        if str(cible).lower() not in reserves and not cible.exists():
            reserves.add(str(cible).lower())
            return cible
        i += 1


@dataclass
class Mouvement:
    audio_src: Path
    audio_dst: Path
    cover_src: Path | None
    cover_dst: Path | None


def previsualiser(plan: Plan) -> list[Mouvement]:
    """Calcule les destinations (sans rien déplacer), collisions résolues."""
    reserves: set[str] = set()
    mouvements: list[Mouvement] = []
    for sa in plan.a_traiter:
        singles = sa.artiste / NOM_DOSSIER_SINGLES
        audio_dst = _nom_libre(singles, sa.audio.name, reserves)
        cover_dst = None
        if sa.cover is not None:
            cover_dst = _nom_libre(
                singles, f"cover_{audio_dst.stem}{sa.cover.suffix.lower()}", reserves
            )
        mouvements.append(
            Mouvement(sa.audio, audio_dst, sa.cover, cover_dst)
        )
    return mouvements


def appliquer(
    plan: Plan,
    racine: str | Path,
    *,
    log: Callable[[str], None] | None = None,
) -> Path:
    """Déplace les singles, supprime les dossiers album vidés, écrit un journal.

    :return: chemin du journal d'annulation.
    """
    def _log(m: str) -> None:
        if log:
            log(m)

    journal: list[dict] = []
    for sa, mv in zip(plan.a_traiter, previsualiser(plan)):
        mv.audio_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(mv.audio_src), str(mv.audio_dst))
        journal.append({"type": "move", "de": str(mv.audio_dst), "vers": str(mv.audio_src)})
        if sa.cover is not None and mv.cover_dst is not None:
            shutil.move(str(mv.cover_src), str(mv.cover_dst))
            journal.append({"type": "move", "de": str(mv.cover_dst), "vers": str(mv.cover_src)})
        # Nettoie les fichiers junk puis retire le dossier album s'il est vide.
        for j in sa.junk:
            j.unlink(missing_ok=True)
        try:
            sa.album.rmdir()
            journal.append({"type": "rmdir", "path": str(sa.album)})
            _log(f"✓ {sa.album.name} → {NOM_DOSSIER_SINGLES}/")
        except OSError:
            _log(f"⚠ {sa.album.name} : non supprimé (contenu restant)")

    chemin = Path(racine) / NOM_JOURNAL
    chemin.write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")
    return chemin


def annuler(racine: str | Path) -> int:
    """Restaure l'état précédent depuis le journal. Retourne le nombre d'actions annulées."""
    chemin = Path(racine) / NOM_JOURNAL
    if not chemin.is_file():
        raise FileNotFoundError(f"Aucun journal d'annulation dans {racine}")

    entrees = json.loads(chemin.read_text(encoding="utf-8"))
    n = 0
    # Ordre inverse : recréer les dossiers, puis y remettre les fichiers.
    for e in reversed(entrees):
        if e["type"] == "rmdir":
            Path(e["path"]).mkdir(parents=True, exist_ok=True)
            n += 1
        elif e["type"] == "move":
            de, vers = Path(e["de"]), Path(e["vers"])
            if de.exists():
                vers.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(de), str(vers))
                n += 1
    return n
