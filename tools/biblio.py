"""Outils de catalogage : tri de cotes de bibliothèque (type Dewey musique)."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Entree:
    artiste: str
    album: str
    cote: str
    brut: str


def parser_lignes(texte: str) -> list[Entree]:
    """Parse des lignes ``Artiste - Album - Cote``.

    La cote est le dernier segment s'il commence par un chiffre (ex. ``786.1 PIN``).
    Sinon l'entrée est conservée sans cote (triée en fin).
    """
    entrees: list[Entree] = []
    for ligne in texte.splitlines():
        ligne = ligne.strip()
        if not ligne:
            continue
        parts = [p.strip() for p in ligne.split(" - ")]
        if len(parts) >= 2 and re.match(r"\d", parts[-1]):
            artiste = parts[0]
            cote = parts[-1]
            album = " - ".join(parts[1:-1])
        else:
            artiste = parts[0]
            album = " - ".join(parts[1:])
            cote = ""
        entrees.append(Entree(artiste=artiste, album=album, cote=cote, brut=ligne))
    return entrees


def parser_csv(texte: str) -> list[Entree]:
    """Parse un CSV à colonnes ``Artiste``, ``Album``, ``Cote`` (cote facultative).

    Les en-têtes sont reconnus sans tenir compte de la casse ni des espaces.
    Une ligne sans cote est conservée (utile pour vérifier l'existence
    artiste/album et récupérer la cote actuelle, sans en connaître une au
    départ).
    """
    lecteur = csv.DictReader(io.StringIO(texte))
    entetes = {
        (nom or "").strip().lower(): nom for nom in (lecteur.fieldnames or [])
    }
    col_artiste = entetes.get("artiste")
    col_album = entetes.get("album")
    col_cote = entetes.get("cote")
    if col_artiste is None or col_album is None:
        raise ValueError(
            "Le CSV doit contenir au moins les colonnes « Artiste » et « Album » "
            "(« Cote » facultative)."
        )

    entrees: list[Entree] = []
    for ligne in lecteur:
        artiste = (ligne.get(col_artiste) or "").strip()
        album = (ligne.get(col_album) or "").strip()
        cote = (ligne.get(col_cote) or "").strip() if col_cote else ""
        if not artiste and not album:
            continue
        brut = " - ".join(p for p in (artiste, album, cote) if p)
        entrees.append(Entree(artiste=artiste, album=album, cote=cote, brut=brut))
    return entrees


def extraire_colonne_artistes(df) -> list[str]:
    """Extrait la colonne « Artiste » d'un tableau (DataFrame pandas), une entrée par ligne.

    En-tête reconnu sans tenir compte de la casse (``artiste`` ou ``artistes``).
    Les cellules vides sont ignorées ; une cellule peut contenir plusieurs noms
    séparés par des virgules (ex. ``"Synapson,Tim Dup,Lass"``) — c'est à
    l'appelant de les rechercher séparément, cette fonction les renvoie tels quels.
    """
    colonnes = {str(c).strip().lower(): c for c in df.columns}
    col = colonnes.get("artiste") or colonnes.get("artistes")
    if col is None:
        raise ValueError("Le fichier doit contenir une colonne « Artiste ».")
    valeurs = df[col].dropna().astype(str).str.strip()
    return [v for v in valeurs if v]


def _cle_cote(e: Entree) -> tuple[float, str]:
    """Clé de tri : partie numérique de la cote (Dewey) puis reste alphanumérique."""
    m = re.match(r"(\d+(?:\.\d+)?)\s*(.*)", e.cote)
    if not m:
        return (float("inf"), e.cote.lower())  # sans cote → à la fin
    return (float(m.group(1)), m.group(2).lower())


def trier_par_cote(entrees: list[Entree]) -> list[Entree]:
    """Trie les entrées par cote croissante (numérique puis alphabétique)."""
    return sorted(entrees, key=_cle_cote)


def formater(entrees: list[Entree]) -> str:
    """Reconstruit le texte trié, une entrée par ligne."""
    return "\n".join(e.brut for e in entrees)


def trier_fichier(chemin: str | Path, sortie: str | Path | None = None) -> Path:
    """Lit un fichier de cotes, le trie et l'écrit (par défaut, écrase la source)."""
    src = Path(chemin)
    entrees = trier_par_cote(parser_lignes(src.read_text(encoding="utf-8")))
    cible = Path(sortie) if sortie else src
    cible.write_text(formater(entrees) + "\n", encoding="utf-8")
    return cible
