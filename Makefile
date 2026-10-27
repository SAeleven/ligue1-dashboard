.PHONY: help setup lint format typecheck test check extract load transform export app

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
extract: ## [J3] API -> couche raw
	uv run python -m ligue1.extract --season $(SEASON)

load: ## [J3] couche raw -> DuckDB
	uv run python -m ligue1.load

transform: ## [J4] dbt build
	cd dbt && uv run dbt build

export: ## [J6] marts -> Parquet
	uv run python -m ligue1.export

app: ## [J5] Lance le dashboard
	uv run streamlit run app/main.py
