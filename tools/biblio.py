"""Outils de catalogage : tri de cotes de bibliothèque (type Dewey musique)."""

from __future__ import annotations

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
