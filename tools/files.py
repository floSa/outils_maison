"""Outils sur les fichiers : nettoyage de noms (slugify) avec annulation."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

NOM_JOURNAL = ".renommage_undo.json"


def nettoyer_nom(
    nom: str,
    *,
    minuscule: bool = True,
    espaces_en: str = "_",
) -> str:
    """Nettoie une chaîne (sans extension) : accents, espaces, caractères spéciaux.

    Étapes : trim → espaces remplacés → accents retirés → on ne garde que
    ``[a-z0-9_-]`` → minuscule (optionnel).
    """
    nom = nom.strip().replace(" ", espaces_en)
    nom = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode("utf-8")
    # Échappe le séparateur pour l'autoriser dans le nom final.
    autorises = re.escape(espaces_en)
    nom = re.sub(rf"[^a-zA-Z0-9{autorises}\-]", "", nom)
    if minuscule:
        nom = nom.lower()
    return nom


@dataclass
class Renommage:
    ancien: Path
    nouveau: Path


def previsualiser(
    dossier: str | Path,
    *,
    extensions: tuple[str, ...] | None = None,
    recursif: bool = False,
    minuscule: bool = True,
) -> list[Renommage]:
    """Calcule les renommages à effectuer, sans rien modifier.

    :param extensions: si fourni, ne traite que ces extensions (ex. ``(".jpg", ".png")``).
                       Sinon, tous les fichiers.
    :param recursif: descend dans les sous-dossiers.
    :return: liste des renommages où le nom change réellement.
    """
    base = Path(dossier)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")

    exts = tuple(e.lower() for e in extensions) if extensions else None
    fichiers = base.rglob("*") if recursif else base.iterdir()

    renommages: list[Renommage] = []
    for f in fichiers:
        if not f.is_file():
            continue
        if exts and f.suffix.lower() not in exts:
            continue
        nouveau_nom = nettoyer_nom(f.stem, minuscule=minuscule) + f.suffix.lower()
        cible = f.with_name(nouveau_nom)
        if cible != f:
            renommages.append(Renommage(ancien=f, nouveau=cible))
    return renommages


def appliquer(renommages: list[Renommage], dossier_journal: str | Path) -> Path:
    """Effectue les renommages et écrit un journal d'annulation.

    Les collisions (cible déjà existante) sont ignorées pour ne pas écraser.
    :return: chemin du journal écrit.
    """
    journal: list[dict[str, str]] = []
    for r in renommages:
        if r.nouveau.exists():
            continue
        r.nouveau.parent.mkdir(parents=True, exist_ok=True)
        r.ancien.rename(r.nouveau)
        journal.append({"de": str(r.nouveau), "vers": str(r.ancien)})

    chemin_journal = Path(dossier_journal) / NOM_JOURNAL
    chemin_journal.write_text(
        json.dumps(journal, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return chemin_journal


def annuler(dossier_journal: str | Path) -> int:
    """Restaure les noms d'origine à partir du journal. Retourne le nb restauré."""
    chemin = Path(dossier_journal) / NOM_JOURNAL
    if not chemin.is_file():
        raise FileNotFoundError(f"Aucun journal d'annulation dans {dossier_journal}")

    entrees = json.loads(chemin.read_text(encoding="utf-8"))
    n = 0
    for e in entrees:
        de, vers = Path(e["de"]), Path(e["vers"])
        if de.exists() and not vers.exists():
            de.rename(vers)
            n += 1
    return n


# --- F2 : renommer en masse (chercher / remplacer) ---------------------------

def previsualiser_remplacement(
    dossier: str | Path,
    chercher: str,
    remplacer: str,
    *,
    regex: bool = False,
    extensions: tuple[str, ...] | None = None,
    recursif: bool = False,
) -> list[Renommage]:
    """Calcule les renommages d'un chercher-remplacer (texte brut ou regex), sans modifier."""
    base = Path(dossier)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")
    if not chercher:
        return []

    exts = tuple(e.lower() for e in extensions) if extensions else None
    fichiers = base.rglob("*") if recursif else base.iterdir()

    renommages: list[Renommage] = []
    for f in fichiers:
        if not f.is_file():
            continue
        if exts and f.suffix.lower() not in exts:
            continue
        if regex:
            nouveau_nom = re.sub(chercher, remplacer, f.name)
        else:
            nouveau_nom = f.name.replace(chercher, remplacer)
        cible = f.with_name(nouveau_nom)
        if cible != f and nouveau_nom:
            renommages.append(Renommage(ancien=f, nouveau=cible))
    return renommages


# --- F3 : doublons de fichiers (par contenu) ---------------------------------

def _hash_fichier(path: Path, taille_bloc: int = 1 << 20) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        while bloc := f.read(taille_bloc):
            h.update(bloc)
    return h.hexdigest()


def trouver_doublons_fichiers(
    dossier: str | Path, *, recursif: bool = True
) -> list[list[Path]]:
    """Regroupe les fichiers strictement identiques (même contenu).

    Pré-filtre par taille (rapide), puis confirme par hash SHA-1.
    Retourne les groupes d'au moins 2 fichiers.
    """
    base = Path(dossier)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")

    it = base.rglob("*") if recursif else base.iterdir()
    par_taille: dict[int, list[Path]] = {}
    for f in it:
        if f.is_file():
            par_taille.setdefault(f.stat().st_size, []).append(f)

    groupes: list[list[Path]] = []
    for candidats in par_taille.values():
        if len(candidats) < 2:
            continue
        par_hash: dict[str, list[Path]] = {}
        for f in candidats:
            par_hash.setdefault(_hash_fichier(f), []).append(f)
        groupes.extend(g for g in par_hash.values() if len(g) > 1)
    return groupes


# --- F1 : arborescence d'un dossier → tableau --------------------------------

def arborescence_vers_df(
    racines: list[str | Path],
    *,
    profondeur_max: int | None = None,
    inclure_fichiers: bool = False,
):
    """Construit un DataFrame de l'arborescence (un niveau de dossier par colonne).

    :param racines: dossiers à explorer.
    :param profondeur_max: profondeur maximale (None = illimitée).
    :param inclure_fichiers: ajoute aussi les fichiers comme feuilles.
    :return: ``pandas.DataFrame`` avec colonnes ``Racine, Niveau 1, Niveau 2, …``.
    """
    import pandas as pd

    lignes: list[list[str]] = []
    for racine in racines:
        base = Path(racine)
        if not base.is_dir():
            continue
        for chemin in base.rglob("*"):
            est_dossier = chemin.is_dir()
            if not inclure_fichiers and not est_dossier:
                continue
            parts = chemin.relative_to(base).parts
            if profondeur_max is not None and len(parts) > profondeur_max:
                continue
            lignes.append([base.name, *parts])

    if not lignes:
        return pd.DataFrame()

    largeur = max(len(l) for l in lignes)
    colonnes = ["Racine"] + [f"Niveau {i}" for i in range(1, largeur)]
    lignes = [l + [""] * (largeur - len(l)) for l in lignes]
    df = pd.DataFrame(lignes, columns=colonnes)
    return df.sort_values(by=colonnes).reset_index(drop=True)


def exporter_excel(df, chemin: str | Path) -> Path:
    """Écrit un DataFrame dans un fichier Excel."""
    cible = Path(chemin)
    cible.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(cible, index=False)
    return cible


# --- F4 : ranger automatiquement par type ou par date ------------------------

CATEGORIES = {
    "Images": (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".heic"),
    "Vidéos": (".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".wmv"),
    "Audio": (".mp3", ".flac", ".wav", ".m4a", ".ogg", ".opus", ".aac", ".wma"),
    "Documents": (".pdf", ".doc", ".docx", ".odt", ".txt", ".xlsx", ".csv", ".pptx", ".md"),
    "Archives": (".zip", ".rar", ".7z", ".tar", ".gz"),
}


def _categorie(suffixe: str) -> str:
    s = suffixe.lower()
    for nom, exts in CATEGORIES.items():
        if s in exts:
            return nom
    return "Autres"


def previsualiser_rangement(
    dossier: str | Path, *, mode: str = "type"
) -> list[Renommage]:
    """Calcule le rangement des fichiers d'un dossier en sous-dossiers (sans modifier).

    :param mode: ``"type"`` (par catégorie d'extension) ou ``"date"`` (année/mois de modif).
    """
    base = Path(dossier)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")
    if mode not in ("type", "date"):
        raise ValueError("mode doit être 'type' ou 'date'.")

    import datetime as _dt

    renommages: list[Renommage] = []
    for f in base.iterdir():
        if not f.is_file():
            continue
        if mode == "type":
            sous = _categorie(f.suffix)
        else:
            d = _dt.datetime.fromtimestamp(f.stat().st_mtime)
            sous = f"{d.year}/{d.month:02d}"
        cible = base / sous / f.name
        if cible != f:
            renommages.append(Renommage(ancien=f, nouveau=cible))
    return renommages


# --- F5 : statistiques d'un dossier ------------------------------------------

def statistiques(dossier: str | Path, *, recursif: bool = True, top: int = 15) -> dict:
    """Statistiques d'un dossier : volume par catégorie, plus gros fichiers, dossiers vides."""
    base = Path(dossier)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")

    it = base.rglob("*") if recursif else base.iterdir()
    par_categorie: dict[str, list[int]] = {}
    tailles: list[tuple[Path, int]] = []
    nb, total = 0, 0
    for f in it:
        if f.is_file():
            taille = f.stat().st_size
            nb += 1
            total += taille
            cat = _categorie(f.suffix)
            agg = par_categorie.setdefault(cat, [0, 0])
            agg[0] += 1
            agg[1] += taille
            tailles.append((f, taille))

    dossiers_vides = [
        d for d in (base.rglob("*") if recursif else base.iterdir())
        if d.is_dir() and not any(d.iterdir())
    ]
    tailles.sort(key=lambda t: t[1], reverse=True)
    return {
        "nb_fichiers": nb,
        "taille_totale": total,
        "par_categorie": par_categorie,
        "plus_gros": tailles[:top],
        "dossiers_vides": dossiers_vides,
    }


# --- F7 : comparer deux dossiers ---------------------------------------------

def comparer_dossiers(
    dossier_a: str | Path, dossier_b: str | Path, *, par_hash: bool = False
) -> dict:
    """Compare deux arborescences (par chemin relatif).

    :param par_hash: si True, compare le contenu (SHA-1) ; sinon la taille (rapide).
    :return: dict avec ``seulement_a``, ``seulement_b``, ``differents`` (chemins relatifs).
    """
    a, b = Path(dossier_a), Path(dossier_b)
    if not a.is_dir() or not b.is_dir():
        raise NotADirectoryError("Les deux dossiers doivent exister.")

    def index(racine: Path) -> dict[str, Path]:
        return {
            str(p.relative_to(racine)).replace("\\", "/"): p
            for p in racine.rglob("*")
            if p.is_file()
        }

    ia, ib = index(a), index(b)
    communs = ia.keys() & ib.keys()
    differents = []
    for rel in sorted(communs):
        fa, fb = ia[rel], ib[rel]
        if par_hash:
            diff = _hash_fichier(fa) != _hash_fichier(fb)
        else:
            diff = fa.stat().st_size != fb.stat().st_size
        if diff:
            differents.append(rel)

    return {
        "seulement_a": sorted(ia.keys() - ib.keys()),
        "seulement_b": sorted(ib.keys() - ia.keys()),
        "differents": differents,
        "identiques": len(communs) - len(differents),
    }


# --- T3 : renommer des fichiers depuis un CSV --------------------------------

def previsualiser_renommage_csv(
    dossier: str | Path,
    csv_path: str | Path,
    *,
    col_ancien: str = "ancien",
    col_nouveau: str = "nouveau",
) -> list[Renommage]:
    """Calcule les renommages depuis un CSV de correspondances (ancien → nouveau).

    Le CSV doit avoir deux colonnes (par défaut ``ancien`` et ``nouveau``) contenant
    les **noms de fichiers** (pas les chemins complets).
    """
    import csv as _csv

    base = Path(dossier)
    if not base.is_dir():
        raise NotADirectoryError(f"Dossier introuvable : {base}")

    renommages: list[Renommage] = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        lecteur = _csv.DictReader(f)
        if col_ancien not in (lecteur.fieldnames or []) or col_nouveau not in (lecteur.fieldnames or []):
            raise ValueError(
                f"Le CSV doit contenir les colonnes « {col_ancien} » et « {col_nouveau} »."
            )
        for ligne in lecteur:
            ancien = (ligne.get(col_ancien) or "").strip()
            nouveau = (ligne.get(col_nouveau) or "").strip()
            if not ancien or not nouveau:
                continue
            src = base / ancien
            if src.is_file():
                cible = base / nouveau
                if cible != src:
                    renommages.append(Renommage(ancien=src, nouveau=cible))
    return renommages
