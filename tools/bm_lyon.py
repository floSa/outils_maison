"""Vérifier la disponibilité de cotes au catalogue BM Lyon (Part-Dieu).

Cas d'usage : on connaît DÉJÀ artiste + album + cote (export précédent) et on
veut re-vérifier le statut ACTUEL ("En rayon", "Prêté - retour prévu le…"),
qui change dans le temps.

Logique de scraping reprise de Musique_Tools (éprouvée sur ~900 albums) :
recherche de l'ARTISTE seul (l'album précis est mal indexé/dispersé), facette
"CD musicaux", scroll lazy-load, filtre auteur sur le libellé en ordre naturel
"Titre [Disque compact] / Prénom Nom", puis lecture du bloc Part-Dieu sur la
fiche du meilleur album.

Deux corrections de bugs à NE PAS régresser (héritées de Musique_Tools) :
- le filtre auteur utilise ``allow_subset=True`` : le catalogue écrit souvent
  un nom de scène seul ("Bourvil") quand on cherche le nom complet ("André
  Bourvil") — sans cette tolérance, des artistes bien réels sont rejetés ;
- le bloc "Part-Dieu\\n<cote> - <statut>" se découpe sur la PREMIÈRE
  occurrence de " - " (``split(" - ", 1)``), car le statut peut lui-même
  contenir " - " ("Prêté - Retour prévu le : 06/08/2026") ; un ``rsplit``
  couperait la cote en deux.

Playwright est importé paresseusement (extra ``scraping``) : tout le matching
reste testable sans navigateur.
"""

from __future__ import annotations

import difflib
import re
import time
import unicodedata
from dataclasses import dataclass, field
from typing import Callable

BM_HOME = "https://catalogue.bm-lyon.fr"
SEUIL_ARTISTE = 0.85
SEUIL_ALBUM = 0.65   # tolérant : suffixes "Deluxe", "Remastered", etc.


# ---------------------------------------------------------------------------
# Matching pur (repris de Musique_Tools/text_match.py, testable sans Playwright)
# ---------------------------------------------------------------------------

def normalize(s: str) -> str:
    """NFKD + ASCII + lowercase + whitespace compressé."""
    if not s:
        return ""
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    return re.sub(r"\s+", " ", s).lower().strip()


def name_similarity(a: str, b: str) -> float:
    """Similarité entre deux noms, robuste à l'inversion prénom/nom.

    Max entre SequenceMatcher direct et version « tokens triés » (le catalogue
    écrit "Cosma, Vladimir" quand l'entrée dit "Vladimir Cosma").
    """
    a_n, b_n = normalize(a), normalize(b)
    if not a_n or not b_n:
        return 0.0
    if a_n == b_n:
        return 1.0
    direct = difflib.SequenceMatcher(None, a_n, b_n).ratio()
    a_sorted = " ".join(sorted(a_n.split()))
    b_sorted = " ".join(sorted(b_n.split()))
    if a_sorted == b_sorted:
        return 1.0
    return max(direct, difflib.SequenceMatcher(None, a_sorted, b_sorted).ratio())


def artist_name_matches(found: str, target: str, allow_subset: bool = False) -> bool:
    """True si ``found`` correspond à ``target`` (seuil 0.85).

    ``allow_subset`` : tolère ``found`` sous-ensemble strict de ``target``
    ("Bourvil" ⊂ "André Bourvil"), tokens ≥ 5 caractères uniquement pour
    éviter "Air" ⊂ "Air Supply".
    """
    if not found or not target:
        return False
    if name_similarity(found, target) >= SEUIL_ARTISTE:
        return True
    if allow_subset:
        f_tokens = set(normalize(found).split())
        t_tokens = set(normalize(target).split())
        if (f_tokens and t_tokens and f_tokens.issubset(t_tokens)
                and all(len(tok) >= 5 for tok in f_tokens)):
            return True
    return False


def parser_notice(txt: str) -> tuple[str, str]:
    """Découpe un libellé de résultat 'Titre [support] / Auteur' en (titre, auteur).

    Sur la page de résultats le libellé est en ordre NATUREL — source la plus
    fiable pour filtrer par auteur.
    """
    if " / " not in txt:
        return txt.split("[")[0].strip(), ""
    left, right = txt.split(" / ", 1)
    title = left.split("[")[0].strip()
    author = re.split(r"[;.]", right)[0].strip()
    return title, author


def extraire_part_dieu(content_text: str) -> tuple[list[str], list[str]]:
    """Parse les blocs "Part-Dieu\\n<cote> - <statut>" d'une fiche détail.

    Retourne (cotes, statuts) alignés. Le découpage se fait sur la PREMIÈRE
    occurrence de " - " : une cote ne contient jamais " - " (espace-tiret-
    espace), mais le statut peut en contenir ("Prêté - Retour prévu le : …").
    """
    cotes: list[str] = []
    statuts: list[str] = []
    lines = content_text.split("\n")
    for idx, line in enumerate(lines):
        if "Part-Dieu" in line and idx + 1 < len(lines):
            next_line = lines[idx + 1].strip()
            if not next_line:
                continue
            if " - " in next_line:
                cote, statut = next_line.split(" - ", 1)
                cote, statut = cote.strip(), statut.strip()
            else:
                cote, statut = next_line, "Voir dispo"
            if cote and cote not in cotes:
                cotes.append(cote)
                statuts.append(statut)
    return cotes, statuts


def cote_equivalente(a: str, b: str) -> bool:
    """Compare deux cotes en tolérant casse/espaces ("786.2 MAL 1" ≡ "786.2  mal 1")."""
    na = re.sub(r"\s+", " ", (a or "")).strip().casefold()
    nb = re.sub(r"\s+", " ", (b or "")).strip().casefold()
    return bool(na) and na == nb


# ---------------------------------------------------------------------------
# Résultat
# ---------------------------------------------------------------------------

@dataclass
class ResultatDispo:
    artiste: str
    album: str
    cote: str
    statut_actuel: str = ""       # ex. "En rayon", "Prêté - Retour prévu le : …"
    statut: str = ""              # OK trouvé / cote non retrouvée / …
    album_trouve: str = ""        # titre du CD retenu au catalogue
    cotes_trouvees: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Scraping (Playwright importé paresseusement)
# ---------------------------------------------------------------------------

def _bm_search_input(page):
    """Champ de recherche du catalogue (plusieurs fallbacks de sélecteur)."""
    for loc in [page.get_by_placeholder("Recherche", exact=False).first,
                page.locator("input[type='search']").first,
                page.locator("input[type='text']").first,
                page.locator("input").first]:
        try:
            if loc.count():
                return loc
        except Exception:
            pass
    return None


def _harvest_artist_cd_notices(page, artist_q: str, max_notices: int = 25) -> list[dict]:
    """Récolte les CD d'un artiste : recherche artiste + facette CD + scroll.

    Retourne [{title, author, href}] dédoublonné par titre.
    """
    if not artist_q:
        return []
    try:
        page.goto(f"{BM_HOME}/", wait_until="domcontentloaded", timeout=20000)
        try:
            page.wait_for_selector("input", timeout=10000)
        except Exception:
            time.sleep(2)
        inp = _bm_search_input(page)
        if inp is None:
            return []
        inp.fill("")
        inp.fill(artist_q)
        inp.press("Enter")
        time.sleep(4)

        # Facette 'CD musicaux' (best-effort) : réduit le bruit DVD/livres.
        try:
            cd = page.get_by_text(re.compile(r"CD musicaux", re.I)).first
            if cd.count():
                cd.click()
                time.sleep(2.5)
        except Exception:
            pass

        # Dérouler jusqu'à stabiliser le nombre de notices (lazy-load).
        prev = -1
        for _ in range(15):
            n = page.locator("a[href*='/notice']").count()
            if n == prev:
                break
            prev = n
            page.mouse.wheel(0, 6000)
            time.sleep(0.8)

        pairs = page.eval_on_selector_all(
            "a[href*='/notice']",
            "els => els.map(e => ({t:(e.textContent||'').replace(/\\s+/g,' ').trim(), href:e.getAttribute('href')||''})).filter(o => o.t)"
        )
    except Exception:
        return []

    out: list[dict] = []
    seen: set = set()
    for o in pairs:
        txt = o["t"]
        if "disque compact" not in normalize(txt):
            continue
        title, author = parser_notice(txt)
        # allow_subset=True indispensable ici (cf. docstring module : Bourvil).
        if not title or not artist_name_matches(author, artist_q, allow_subset=True):
            continue
        key = normalize(title)
        if not key or key in seen:
            continue
        seen.add(key)
        href = o["href"]
        if href.startswith("/"):
            href = BM_HOME + href
        out.append({"title": title, "author": author, "href": href})
        if len(out) >= max_notices:
            break
    return out


def _lire_part_dieu(page, href: str) -> tuple[list[str], list[str]]:
    """Navigue vers une notice et renvoie TOUS les blocs Part-Dieu (cotes, statuts)."""
    try:
        page.goto(href, wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)
        body = page.locator("body").inner_text()
        if "Part-Dieu" in body:
            return extraire_part_dieu(body)
    except Exception:
        pass
    return [], []


def verifier_disponibilites(
    lignes: list[tuple[str, str, str]],
    *,
    log: Callable[[str], None] | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> list[ResultatDispo]:
    """Vérifie la disponibilité actuelle d'une liste de (artiste, album, cote).

    Une seule session Playwright pour tout le lot ; cache des notices par
    artiste (plusieurs albums d'un même artiste = une seule récolte) ; cache
    des blocs Part-Dieu par fiche ; retry simple si une récolte revient vide
    (aléa réseau/timing observé sur de vrais runs).
    """
    from playwright.sync_api import sync_playwright

    def _log(m: str) -> None:
        if log:
            log(m)

    resultats: list[ResultatDispo] = []
    cache_notices: dict[str, list[dict]] = {}
    cache_fiches: dict[str, tuple[list[str], list[str]]] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="fr-FR",
        )
        page = context.new_page()

        for i, (artiste, album, cote) in enumerate(lignes, start=1):
            if progress:
                progress(i, len(lignes))
            res = ResultatDispo(artiste=artiste, album=album, cote=cote)
            resultats.append(res)
            if not artiste or not cote:
                res.statut = "ligne invalide"
                continue

            try:
                cle = normalize(artiste)
                if cle in cache_notices:
                    notices = cache_notices[cle]
                else:
                    _log(f"🔍 {artiste} : recherche au catalogue…")
                    notices = _harvest_artist_cd_notices(page, artiste)
                    if not notices:
                        # Retry : un artiste réel peut échouer sur un aléa
                        # réseau/timing (cas observé : Gaëtan Roussel).
                        _log(f"   ↻ {artiste} : aucun résultat, nouvelle tentative…")
                        time.sleep(2)
                        notices = _harvest_artist_cd_notices(page, artiste)
                    cache_notices[cle] = notices

                if not notices:
                    res.statut = "artiste non trouvé au catalogue"
                    _log(f"   ❌ {artiste} : absent du catalogue")
                    continue

                # Meilleur album par similarité de titre.
                best, best_s = None, 0.0
                for nt in notices:
                    s = name_similarity(nt["title"], album)
                    if s > best_s:
                        best_s, best = s, nt
                if not best or best_s < SEUIL_ALBUM:
                    res.statut = "album non retrouvé"
                    _log(f"   ❌ {artiste} — {album} : album absent "
                         f"(meilleur titre à {best_s:.2f})")
                    continue
                res.album_trouve = best["title"]

                if best["href"] in cache_fiches:
                    cotes, statuts = cache_fiches[best["href"]]
                else:
                    cotes, statuts = _lire_part_dieu(page, best["href"])
                    cache_fiches[best["href"]] = (cotes, statuts)
                res.cotes_trouvees = cotes

                # Comparer à LA cote fournie (plusieurs exemplaires possibles).
                trouve = False
                for c, s in zip(cotes, statuts):
                    if cote_equivalente(c, cote):
                        res.statut = "OK trouvé"
                        res.statut_actuel = s
                        trouve = True
                        _log(f"   ✅ {artiste} — {album} [{cote}] : {s}")
                        break
                if not trouve:
                    res.statut = "cote non retrouvée, à vérifier manuellement"
                    _log(f"   ⚠️ {artiste} — {album} : cote {cote!r} absente "
                         f"de la fiche (trouvé : {cotes or 'aucune'})")

            except Exception as e:
                res.statut = "erreur réseau"
                _log(f"   💥 {artiste} — {album} : {e}")

        browser.close()
    return resultats
