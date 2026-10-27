# Ligue 1 Dashboard

![CI](https://github.com/<ton-compte>/ligue1-dashboard/actions/workflows/ci.yml/badge.svg)

Dashboard public de la saison de Ligue 1 en cours, alimenté chaque jour par un pipeline de données automatisé :

```
football-data.org ──▶ JSON (raw) ──▶ DuckDB ──▶ dbt (staging → intermediate → marts) ──▶ Parquet ──▶ Streamlit
                        └──────────── orchestré par GitHub Actions, chaque jour à 6 h ────────────┘
```

> 🚧 Projet en cours — jalon actuel : **J2 Setup**. Voir le [cahier des charges](docs/cdc.md) et la [spécification technique](docs/spec.md).

## Stack

Python 3.12 · httpx · Pydantic · DuckDB · dbt-core · Streamlit · GitHub Actions · uv · ruff · mypy · pytest

## Démarrage rapide

Prérequis : [uv](https://docs.astral.sh/uv/getting-started/installation/) et `make`.

```bash
git clone https://github.com/<ton-compte>/ligue1-dashboard.git
cd ligue1-dashboard
make setup                 # installe Python 3.12, les dépendances et les hooks pre-commit
cp .env.example .env       # puis renseigner FOOTBALL_DATA_TOKEN
make check                 # lint + typage + tests
```

Un token gratuit s'obtient sur [football-data.org](https://www.football-data.org/client/register).

## Commandes

| Commande | Rôle |
| --- | --- |
| `make setup` | Environnement + hooks pre-commit |
| `make check` | Lint, typage, tests (comme la CI) |
| `make format` | Formate le code |
| `make extract` | *(J3)* API → couche raw |
| `make load` | *(J3)* raw → DuckDB |
| `make transform` | *(J4)* `dbt build` |
| `make app` | *(J5)* Lance le dashboard |

## Arborescence

```
├── .github/workflows/   CI (et pipeline quotidien en J6)
├── app/                 dashboard Streamlit (J5)
├── src/ligue1/          ingestion : client API, extract, load, export
├── dbt/                 modèles staging / intermediate / marts + tests (J4)
├── tests/               tests pytest
└── docs/                cahier des charges, spec, ADR
```

## Avancement

- [x] J1 Cadrage — cahier des charges et spécification technique
- [x] J2 Setup — repo, uv, pre-commit, CI
- [ ] J3 Ingestion
- [ ] J4 Modélisation dbt
- [ ] J5 Dashboard
- [ ] J6 Automatisation et mise en ligne
- [ ] J7 Finalisation

## Données

Données fournies par [football-data.org](https://www.football-data.org/) (offre gratuite).
