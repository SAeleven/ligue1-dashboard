.PHONY: help setup lint format typecheck test check extract load transform docs export app

SEASON ?= 2026

help: ## Liste les commandes
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  %-10s %s\n", $$1, $$2}'

setup: ## Installe l'environnement et les hooks pre-commit
	uv sync
	uv run pre-commit install

lint: ## Lint et vérification du format
	uv run ruff check .
	uv run ruff format --check .

format: ## Formate le code
	uv run ruff check --fix .
	uv run ruff format .

typecheck: ## Typage strict
	uv run mypy

test: ## Tests pytest
	uv run pytest

check: lint typecheck test ## Tout ce que la CI vérifie

# --- Pipeline (implémenté aux jalons suivants) ---------------------------------
extract: ## API -> couche raw (SEASON=2026, SCORERS=1 pour tenter les buteurs)
	uv run python -m ligue1.extract --season $(SEASON) $(if $(SCORERS),--scorers,)

load: ## couche raw -> DuckDB (schéma raw)
	uv run python -m ligue1.load

transform: ## dbt build (modèles + tests)
	uv run dbt build --project-dir dbt --profiles-dir dbt

docs: ## Génère et sert la documentation dbt (lineage)
	uv run dbt docs generate --project-dir dbt --profiles-dir dbt
	uv run dbt docs serve --project-dir dbt --profiles-dir dbt

export: ## [J6] marts -> Parquet
	uv run python -m ligue1.export

app: ## [J5] Lance le dashboard
	uv run streamlit run app/main.py
