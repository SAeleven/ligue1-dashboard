# ADR 0001 — Outillage Python

- Statut : accepté
- Date : 2026-10-27

## Contexte

Le projet doit être installable en moins de 10 minutes (NF5) et typé, linté, testé, avec une CI verte sur chaque push (NF9). L'outillage doit être identique en local, dans pre-commit et en CI.

## Décision

- **uv** gère Python 3.12 (`.python-version`), les dépendances (`pyproject.toml`) et le verrouillage (`uv.lock`, commité). La CI installe avec `uv sync --locked`.
- **ruff** fait le lint et le formatage ; **mypy** en mode strict ; **pytest** (+ `respx` pour simuler l'API).
- Les hooks pre-commit ruff et mypy appellent `uv run` plutôt que des dépôts de hooks externes : une seule source de vérité pour les versions.
- Layout `src/` : le package `ligue1` n'est importable qu'une fois installé, ce qui évite les imports accidentels depuis la racine.
- Les dépendances dbt et Streamlit seront ajoutées à leurs jalons (J4, J5) pour garder l'environnement léger.

## Conséquences

- Un contributeur n'a besoin que de `uv` ; `make setup` suffit.
- Toute nouvelle dépendance passe par `uv add` et met à jour `uv.lock`.
