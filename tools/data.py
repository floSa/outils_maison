"""Outils données : conversion entre tableaux (CSV, Excel, JSON)."""

from __future__ import annotations

from pathlib import Path

FORMATS = ("csv", "xlsx", "json")


def _lire(src: Path):
    import pandas as pd

    ext = src.suffix.lower().lstrip(".")
    if ext == "csv":
        return pd.read_csv(src)
    if ext in ("xlsx", "xls"):
        return pd.read_excel(src)
    if ext == "json":
        return pd.read_json(src)
    raise ValueError(f"Format d'entrée non géré : .{ext}")


def convertir_tableau(
    src: str | Path, format_sortie: str, sortie: str | Path | None = None
):
    """Convertit un tableau d'un format à un autre (CSV ↔ Excel ↔ JSON).

    :param format_sortie: ``csv``, ``xlsx`` ou ``json``.
    :return: chemin du fichier écrit.
    """
    src = Path(src)
    if not src.is_file():
        raise FileNotFoundError(f"Fichier introuvable : {src}")
    fmt = format_sortie.lower().lstrip(".")
    if fmt not in FORMATS:
        raise ValueError(f"Format de sortie non géré : {fmt} (choix : {', '.join(FORMATS)})")

    df = _lire(src)
    cible = Path(sortie) if sortie else src.with_suffix(f".{fmt}")

    if fmt == "csv":
        df.to_csv(cible, index=False)
    elif fmt == "xlsx":
        df.to_excel(cible, index=False)
    else:  # json
        df.to_json(cible, orient="records", force_ascii=False, indent=2)
    return cible
