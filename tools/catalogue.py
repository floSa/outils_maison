"""Cataloguer les albums d'une bibliothèque musicale (NAS) en CSV.

Source : une racine (typiquement ``M:\\musiques``) contenant des **dossiers de
catégorie** à sa racine. Deux structures coexistent, et le choix se fait
**uniquement sur le nom du dossier** — pas de détection automatique de profondeur.

- Dossiers « artistes » (par défaut ``__autres``) → structure à 3 niveaux ::

      <racine>\\__autres\\<Artiste>\\<Album>\\<fichiers audio>

  Chaque album émet ``(Artiste, Album)``.

- Toute autre catégorie → structure à 2 niveaux ::

      <racine>\\<Categorie>\\<Album>\\<fichiers audio>

  Chaque album émet ``(nom_categorie, Album)``.

On ne descend **jamais** plus profond : un album multi-disques (``Album\\CD 01``,
``Album\\CD 02``) produit **une seule ligne**, celle de ``Album``.

Le CSV de sortie a deux colonnes (en-tête ``artiste_ou_categorie;album``),
séparateur ``;``, encodage ``utf-8-sig`` (accents corrects dans Excel FR), fins
de ligne ``\\r\\n``. Le tri est alphabétique sur la colonne A puis la colonne B,
insensible à la casse et aux accents (clé de tri seulement — la valeur écrite
reste l'originale).

Lecture **strictement** en lecture seule : aucun accès aux fichiers eux-mêmes
(seulement aux noms de dossiers, via ``os.scandir`` pour limiter les appels
réseau), aucune écriture, aucun renommage sous la racine scannée.
"""

from __future__ import annotations

import csv
import io
import os
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

EN_TETE = ("artiste_ou_categorie", "album")
DOSSIERS_ARTISTES_DEFAUT = ("__autres",)


class RacineIndisponible(RuntimeError):
    """La racine à scanner est introuvable ou inaccessible (lecteur réseau non monté)."""


@dataclass
class CategorieStat:
    nom: str
    est_dossier_artistes: bool  # True → structure à 3 niveaux
    nb_albums: int
    nb_artistes: int = 0  # renseigné uniquement pour les dossiers « artistes »


@dataclass
class Catalogue:
    lignes: list[tuple[str, str]] = field(default_factory=list)
    stats: list[CategorieStat] = field(default_factory=list)
    avertissements: list[str] = field(default_factory=list)

    @property
    def total_albums(self) -> int:
        return len(self.lignes)


def _cle_tri(valeur: str) -> str:
    """Clé de tri insensible à la casse et aux accents (la valeur reste intacte)."""
    return unicodedata.normalize("NFKD", valeur).casefold()


def _est_ignore(nom: str) -> bool:
    """Dossier système / caché : nom commençant par un point.

    On ne filtre **pas** ``_`` : les catégories s'appellent ``__autres``, ``__MUZAK``.
    """
    return nom.startswith(".")


def _sous_dossiers(chemin: Path, avertissements: list[str]) -> list[os.DirEntry]:
    """Sous-dossiers directs de ``chemin`` (hors dossiers cachés), triés par nom.

    Un dossier illisible (permission, I/O réseau, chemin > 260 caractères sous
    Windows) est ajouté aux avertissements et traité comme vide : le scan continue.
    """
    entrees: list[os.DirEntry] = []
    try:
        with os.scandir(chemin) as it:
            for entree in it:
                if _est_ignore(entree.name):
                    continue
                try:
                    if entree.is_dir():
                        entrees.append(entree)
                except OSError as e:  # is_dir() peut échouer sur un chemin trop long
                    avertissements.append(f"{entree.path} : {e}")
    except OSError as e:
        avertissements.append(f"{chemin} : {e}")
        return []
    entrees.sort(key=lambda e: _cle_tri(e.name))
    return entrees


def scanner(
    racine: str | Path,
    dossiers_artistes: tuple[str, ...] = DOSSIERS_ARTISTES_DEFAUT,
) -> Catalogue:
    """Parcourt ``racine`` et produit le catalogue trié (lignes, stats, avertissements).

    :raises RacineIndisponible: si la racine est introuvable ou inaccessible
        (lecteur réseau non monté, partage déconnecté).
    """
    base = Path(racine)
    artistes = set(dossiers_artistes)
    avertissements: list[str] = []

    # La racine elle-même est le seul point où l'inaccessibilité est fatale.
    try:
        categories = list(os.scandir(base))
    except OSError as e:
        raise RacineIndisponible(
            f"Racine inaccessible : {base}. Le lecteur réseau semble indisponible "
            f"(non monté ou partage déconnecté). Détail : {e}"
        ) from e

    categories = [
        c for c in categories if not _est_ignore(c.name) and _dossier_sur(c, avertissements)
    ]
    categories.sort(key=lambda c: _cle_tri(c.name))

    lignes: list[tuple[str, str]] = []
    stats: list[CategorieStat] = []

    for cat in categories:
        cat_path = Path(cat.path)
        if cat.name in artistes:
            # 3 niveaux : catégorie → artistes → albums.
            nb_artistes = nb_albums = 0
            for artiste in _sous_dossiers(cat_path, avertissements):
                nb_artistes += 1
                for album in _sous_dossiers(Path(artiste.path), avertissements):
                    lignes.append((artiste.name, album.name))
                    nb_albums += 1
            stats.append(
                CategorieStat(cat.name, True, nb_albums, nb_artistes=nb_artistes)
            )
        else:
            # 2 niveaux : catégorie → albums.
            albums = _sous_dossiers(cat_path, avertissements)
            for album in albums:
                lignes.append((cat.name, album.name))
            stats.append(CategorieStat(cat.name, False, len(albums)))

    lignes.sort(key=lambda t: (_cle_tri(t[0]), _cle_tri(t[1])))
    return Catalogue(lignes=lignes, stats=stats, avertissements=avertissements)


def _dossier_sur(entree: os.DirEntry, avertissements: list[str]) -> bool:
    try:
        return entree.is_dir()
    except OSError as e:
        avertissements.append(f"{entree.path} : {e}")
        return False


def _sous_la_racine(cible: Path, racine: Path) -> bool:
    """Vrai si ``cible`` est la racine ou se trouve à l'intérieur (chemins résolus)."""
    cible, racine = cible.resolve(), racine.resolve()
    return cible == racine or racine in cible.parents


def csv_texte(catalogue: Catalogue) -> str:
    """Sérialise le catalogue en texte CSV (``;``, fins de ligne ``\\r\\n``).

    Le texte est encodé en ``utf-8-sig`` par l'appelant (fichier ou téléchargement).
    """
    tampon = io.StringIO(newline="")
    ecrivain = csv.writer(tampon, delimiter=";")
    ecrivain.writerow(EN_TETE)
    ecrivain.writerows(catalogue.lignes)
    return tampon.getvalue()


def ecrire_csv(catalogue: Catalogue, chemin: str | Path, racine: str | Path) -> Path:
    """Écrit le CSV sur disque en ``utf-8-sig``.

    :raises ValueError: si ``chemin`` est situé sous ``racine`` (interdiction stricte
        d'écrire dans la bibliothèque scannée).
    """
    cible = Path(chemin)
    if _sous_la_racine(cible, Path(racine)):
        raise ValueError(
            f"Refus d'écrire sous la racine scannée : « {cible} » est dans « {racine} ». "
            "Choisis une destination hors de la bibliothèque (Bureau, Téléchargements…)."
        )
    cible.parent.mkdir(parents=True, exist_ok=True)
    # newline="" : csv gère lui-même les fins de ligne \r\n.
    with open(cible, "w", encoding="utf-8-sig", newline="") as f:
        f.write(csv_texte(catalogue))
    return cible


def recap(catalogue: Catalogue, racine: str | Path) -> str:
    """Récapitulatif textuel de l'interprétation de la structure (contrôle avant CSV)."""
    lignes = [f"Racine : {racine}"]
    largeur = max((len(s.nom) for s in catalogue.stats), default=0)
    for s in catalogue.stats:
        if s.est_dossier_artistes:
            detail = f"{s.nb_artistes} artistes, {s.nb_albums} albums"
        else:
            detail = f"{s.nb_albums} albums"
        lignes.append(f"  {s.nom.ljust(largeur)} : {detail}")
    lignes.append("  ---")
    lignes.append(
        f"  Total : {catalogue.total_albums} albums sur {len(catalogue.stats)} catégories"
    )
    return "\n".join(lignes)
