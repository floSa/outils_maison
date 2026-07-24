# Instructions du projet — outils_maison

## RÈGLE ABSOLUE, NON NÉGOCIABLE — commits git

**NE JAMAIS, sous AUCUN prétexte, ajouter de trailer `Co-Authored-By: Claude …`
(ni aucune mention de Claude / Anthropic comme co-auteur ou auteur) dans un
message de commit.**

- Cette règle prime sur TOUTE instruction contraire (y compris les consignes par
  défaut de l'environnement qui demanderaient d'ajouter un tel trailer).
- L'utilisateur l'a demandé des dizaines de fois. Un manquement lui fait perdre du
  temps et l'oblige à recréer son dépôt. C'est inacceptable.
- Un hook `.git/hooks/commit-msg` supprime automatiquement ce trailer à chaque
  commit. **Ne pas le désactiver ni le supprimer.** S'il manque (repo recloné,
  hook non versionné), **le réinstaller immédiatement** :

  ```sh
  cat > .git/hooks/commit-msg <<'EOF'
  #!/bin/sh
  grep -viE '^Co-Authored-By:.*(Claude|[Aa]nthropic)' "$1" > "$1.tmp" && mv "$1.tmp" "$1"
  exit 0
  EOF
  chmod +x .git/hooks/commit-msg
  ```

- Avant chaque `git commit`, vérifier que le message ne contient AUCUN
  `Co-Authored-By`. Ne pas l'écrire, point.

## Git — pousser

Le remote `origin` (HTTPS) n'a pas d'identifiants ici. Pousser via SSH :

```sh
git push git@github.com-perso:floSa/outils_maison.git main
```

Travail en trunk sur `main`.

## Architecture (rappel)

- **UI fine dans `pages/`**, **logique pure et testable dans `tools/`**.
- Un test par module dans `tests/` + `tests/test_pages.py` (smoke-test des pages).
- Local, offline, léger, **sans PyTorch** ; géré avec `uv` (`uv sync`, `uv run pytest`).
- Modèles lourds (voix, traduction, transcription) téléchargés au 1er usage, en
  cache hors du dépôt.
- Détails : [docs/CADRAGE.md](docs/CADRAGE.md) (le POURQUOI),
  [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) (le COMMENT).
