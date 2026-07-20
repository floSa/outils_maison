"""Regrouper les « singles » d'une bibliothèque musicale.

Arborescence attendue : racine / <artiste> / <album> / fichiers.
Un dossier album qui ne contient **qu'un seul fichier audio** (avec éventuellement
des pochettes ou fichiers annexes) est un « single ». L'outil :

- déplace le titre dans ``<artiste>/Singles/`` en **retirant son numéro de piste**
  (``01 - Ring Ring.flac`` → ``Singles/Ring Ring.flac``) ;
- déplace ses fichiers annexes (pochettes, .nfo, .cue…) dans ``Singles/``, renommés
  au titre (``Cover.jpg`` → ``Ring Ring.jpg``), plusieurs pochettes gérées ;
- **ne supprime rien** : le dossier d'album vidé est déplacé dans un unique dossier
  ``<racine>/_albums_vides_a_supprimer/`` que l'utilisateur pourra supprimer d'un
  clic (interface web du NAS). Aucune perte de fichier.

Sécurité : aperçu avant action, journal d'annulation, et tout dossier au contenu
inattendu (sous-dossier, fichier d'un type non reconnu) est signalé et laissé tel quel.
Le retrait du numéro n'a lieu que si un séparateur suit (``01 - Titre``, ``01. Titre``)
pour ne pas amputer un titre commençant par un nombre (``99 Luftballons``).
"""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

EXT_AUDIO = (".flac", ".mp3", ".m4a", ".wav", ".ogg", ".opus", ".wma", ".aac", ".aiff", ".alac")
# Fichiers annexes déplacés avec le single (pochettes et métadonnées).
SIDECAR_EXT = (
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff",
    ".pdf", ".txt", ".log", ".cue", ".nfo", ".lrc",
)
FICHIERS_JUNK = {"thumbs.db", ".ds_store", "desktop.ini"}
NOM_DOSSIER_SINGLES = "Singles"
NOM_CORBEILLE = "_albums_vides_a_supprimer"
NOM_JOURNAL = ".singles_undo.json"

# Numéro de piste en tête. Deux formes retirées :
#   - numéro suivi d'un séparateur : « 01 - », « 01. », « 01) » ;
#   - numéro **à zéro devant** suivi d'un espace : « 01 », « 02 »… (sans ambiguïté).
# Un nombre non zéro-paddé sans séparateur est laissé (« 99 Luftballons », « 7 Years »).
_RE_NUM_PISTE = re.compile(r"^\s*(?:\d{1,3}\s*[-.)]\s*|0\d{1,2}\s+)")


def _titre_sans_numero(stem: str) -> str:
    """Retire le préfixe de numéro de piste. ``01 - Ring Ring`` / ``01 Ring Ring`` → ``Ring Ring``."""
    return _RE_NUM_PISTE.sub("", stem).strip() or stem


@dataclass
class AlbumSingle:
    artiste: Path
    album: Path
    audio: Path
    sidecars: list[Path] = field(default_factory=list)  # pochettes / annexes à déplacer
    junk: list[Path] = field(default_factory=list)       # Thumbs.db… (partent en corbeille)
    autres: list[Path] = field(default_factory=list)     # contenu inattendu → à vérifier

    @property
    def a_verifier(self) -> bool:
        return bool(self.autres)


@dataclass
class Plan:
    a_traiter: list[AlbumSingle]
    a_verifier: list[AlbumSingle]


def _classer(album: Path) -> AlbumSingle | None:
    """Analyse un dossier album (via os.scandir). AlbumSingle si exactement 1 audio, sinon None."""
    audios, sidecars, junk, autres, sous_dossiers = [], [], [], [], []
    try:
        with os.scandir(album) as it:
            for e in it:
                try:
                    est_dossier = e.is_dir()
                except OSError:
                    autres.append(Path(e.path))
                    continue
                if est_dossier:
                    sous_dossiers.append(Path(e.path))
                    continue
                nom = e.name
                ext = os.path.splitext(nom)[1].lower()
                if nom.lower() in FICHIERS_JUNK:
                    junk.append(Path(e.path))
                elif ext in EXT_AUDIO:
                    audios.append(Path(e.path))
                elif ext in SIDECAR_EXT:
                    sidecars.append(Path(e.path))
                else:
                    autres.append(Path(e.path))
    except OSError:
        return None

    if len(audios) != 1:
        return None  # vrai album (0 ou plusieurs audios), ou multi-disques (sous-dossiers)

    # Plusieurs pochettes sont acceptées. Seuls un sous-dossier ou un fichier d'un
    # type non reconnu rendent le dossier « à vérifier » (non traité).
    return AlbumSingle(
        artiste=album.parent,
        album=album,
        audio=audios[0],
        sidecars=sorted(sidecars),
        junk=junk,
        autres=autres + sous_dossiers,
    )


def _sous_dossiers(chemin: Path) -> list[Path]:
    """Sous-dossiers directs, hors ``.``/``_`` (ignore la corbeille et les dossiers système)."""
    out: list[Path] = []
    try:
        with os.scandir(chemin) as it:
            for e in it:
                if e.name.startswith((".", "_")):
                    continue
                try:
                    if e.is_dir():
                        out.append(Path(e.path))
                except OSError:
                    continue
    except OSError:
        return []
    return sorted(out)


def analyser(
    racine: str | Path,
    *,
    progress: Callable[[int, int], None] | None = None,
) -> Plan:
    """Parcourt racine/<artiste>/<album> et classe les dossiers single.

    :param progress: rappelé après chaque artiste avec ``(traités, total)``.
    :return: Plan(a_traiter, a_verifier).
    """
    base = Path(racine)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")

    a_traiter: list[AlbumSingle] = []
    a_verifier: list[AlbumSingle] = []
    artistes = _sous_dossiers(base)
    total = len(artistes)
    for i, artiste in enumerate(artistes, 1):
        for album in _sous_dossiers(artiste):
            if album.name.lower() == NOM_DOSSIER_SINGLES.lower():
                continue  # ne pas retraiter un dossier Singles existant
            sa = _classer(album)
            if sa is None:
                continue
            (a_verifier if sa.a_verifier else a_traiter).append(sa)
        if progress:
            progress(i, total)
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
    sidecars: list[tuple[Path, Path]] = field(default_factory=list)  # (src, dst)


def previsualiser(plan: Plan) -> list[Mouvement]:
    """Calcule les destinations (sans rien déplacer), collisions résolues."""
    reserves: set[str] = set()
    mouvements: list[Mouvement] = []
    for sa in plan.a_traiter:
        singles = sa.artiste / NOM_DOSSIER_SINGLES
        titre = _titre_sans_numero(sa.audio.stem)
        audio_dst = _nom_libre(singles, titre + sa.audio.suffix.lower(), reserves)
        sidecar_mvs: list[tuple[Path, Path]] = []
        for sc in sa.sidecars:
            dst = _nom_libre(singles, titre + sc.suffix.lower(), reserves)
            sidecar_mvs.append((sc, dst))
        mouvements.append(Mouvement(sa.audio, audio_dst, sidecar_mvs))
    return mouvements


@dataclass
class ResultatSingles:
    journal: Path
    nb_singles: int
    nb_en_corbeille: int
    erreurs: list[str] = field(default_factory=list)


def _est_vide_sauf_junk(album: Path) -> bool:
    """Vrai si le dossier ne contient plus que d'éventuels fichiers junk."""
    try:
        with os.scandir(album) as it:
            for e in it:
                if e.name.lower() not in FICHIERS_JUNK:
                    return False
    except OSError:
        return False
    return True


def appliquer(
    plan: Plan,
    racine: str | Path,
    *,
    log: Callable[[str], None] | None = None,
) -> ResultatSingles:
    """Déplace les singles + annexes, met les dossiers vidés en corbeille, écrit un journal.

    Ne supprime aucun fichier. Résilient : une erreur sur un single est collectée
    et le traitement continue. Retourne un ResultatSingles.
    """
    def _log(m: str) -> None:
        if log:
            log(m)

    journal: list[dict] = []
    erreurs: list[str] = []
    reserves_corbeille: set[str] = set()
    corbeille = Path(racine) / NOM_CORBEILLE
    nb_singles = nb_corbeille = 0

    for sa, mv in zip(plan.a_traiter, previsualiser(plan)):
        try:
            mv.audio_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(mv.audio_src), str(mv.audio_dst))
            journal.append({"type": "move", "de": str(mv.audio_dst), "vers": str(mv.audio_src)})
            for src, dst in mv.sidecars:
                shutil.move(str(src), str(dst))
                journal.append({"type": "move", "de": str(dst), "vers": str(src)})
        except OSError as e:
            erreurs.append(f"{sa.album} : {e}")
            continue
        nb_singles += 1

        # Le dossier ne contient plus que du junk → on déplace TOUT le dossier
        # (junk compris) en corbeille. Rien n'est supprimé par l'outil.
        if _est_vide_sauf_junk(sa.album):
            dest = _nom_libre(corbeille / sa.artiste.name, sa.album.name, reserves_corbeille)
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(sa.album), str(dest))
                journal.append({"type": "move", "de": str(dest), "vers": str(sa.album)})
                nb_corbeille += 1
                _log(f"✓ {sa.album.name} → {NOM_DOSSIER_SINGLES}/ (dossier vidé → corbeille)")
            except OSError as e:
                erreurs.append(f"{sa.album} (mise en corbeille) : {e}")
        else:
            _log(f"⚠ {sa.album.name} : contenu inattendu restant, dossier laissé en place")

    chemin = Path(racine) / NOM_JOURNAL
    try:
        chemin.write_text(json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as e:
        erreurs.append(f"Journal d'annulation non écrit ({chemin}) : {e}")
    return ResultatSingles(
        journal=chemin, nb_singles=nb_singles, nb_en_corbeille=nb_corbeille, erreurs=erreurs
    )


def annuler(racine: str | Path) -> int:
    """Restaure l'état précédent depuis le journal. Retourne le nombre d'actions annulées."""
    chemin = Path(racine) / NOM_JOURNAL
    if not chemin.is_file():
        raise FileNotFoundError(f"Aucun journal d'annulation dans {racine}")

    entrees = json.loads(chemin.read_text(encoding="utf-8"))
    n = 0
    # Ordre inverse : d'abord ressortir le dossier de la corbeille, puis y remettre
    # les fichiers (les deux sont des « move »). Compat : ancien type « rmdir ».
    for e in reversed(entrees):
        if e.get("type") == "rmdir":  # journaux antérieurs
            Path(e["path"]).mkdir(parents=True, exist_ok=True)
            n += 1
        else:  # "move"
            de, vers = Path(e["de"]), Path(e["vers"])
            if de.exists() and not vers.exists():
                vers.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(de), str(vers))
                n += 1
    return n
