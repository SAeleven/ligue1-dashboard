# Ligue 1 Dashboard

![CI](https://github.com/SAeleven/ligue1-dashboard/actions/workflows/ci.yml/badge.svg)
![Pipeline quotidien](https://github.com/SAeleven/ligue1-dashboard/actions/workflows/pipeline.yml/badge.svg)

**▶ Dashboard en ligne : [ligue1-dashboard.streamlit.app](https://ligue1-dashboard.streamlit.app/)**

Dashboard public de la saison de Ligue 1 en cours, alimenté chaque jour par un pipeline de données automatisé :

```
football-data.org ──▶ JSON (raw) ──▶ DuckDB ──▶ dbt (staging → intermediate → marts) ──▶ Parquet ──▶ Streamlit
                        └──────────── orchestré par GitHub Actions, chaque jour à 6 h ────────────┘
```

> 🚧 Projet en cours — jalon actuel : **J6 Automatisation** (validation : 7 jours de mises à jour automatiques). Voir le [cahier des charges](docs/cdc.md) et la [spécification technique](docs/spec.md).

## Stack

Python 3.12 · httpx · Pydantic · DuckDB · dbt-core · Streamlit · GitHub Actions · uv · ruff · mypy · pytest

## Démarrage rapide

Prérequis : [uv](https://docs.astral.sh/uv/getting-started/installation/) et `make`.

```bash
git clone https://github.com/SAeleven/ligue1-dashboard.git
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
| `make extract` | API → couche raw (`data/raw/…`) ; `SCORERS=1` pour tenter les buteurs |
| `make load` | raw → DuckDB (schéma `raw`) |
| `make transform` | `dbt build` : modèles + tests |
| `make docs` | Documentation dbt et lineage |
| `make export` | marts → Parquet (`data/marts`) |
| `make app` | Lance le dashboard sur http://localhost:8501 |

## Mise à jour quotidienne et mise en ligne

Le workflow [`pipeline.yml`](.github/workflows/pipeline.yml) tourne chaque jour à 5 h UTC (et à la demande depuis l'onglet *Actions*) : extract → load → `dbt build` → export Parquet, puis publication sur la branche orpheline [`data`](../../tree/data). Un test dbt en échec bloque la publication : le dashboard garde les données de la veille. Détails : [ADR 0003](docs/adr/0003-publication-des-donnees.md).

Le dashboard hébergé (Streamlit Community Cloud) lit les Parquet de la branche `data` par HTTPS via le secret `MARTS_URL` ; il installe uniquement [`app/requirements.txt`](app/requirements.txt).

Mettre à jour les données en local :

```bash
make extract SCORERS=1 && make load && make transform
```

## Arborescence

```
├── .github/workflows/   ci.yml (qualité, à chaque push), pipeline.yml (données, chaque jour)
├── app/                 dashboard Streamlit : main.py, data.py, blocks/ (F1 à F5)
├── src/ligue1/          ingestion : client API, extract, load, export
├── dbt/                 modèles staging / intermediate / marts + tests (J4)
├── tests/               tests pytest
└── docs/                cahier des charges, spec, ADR
```

## Avancement

- [x] J1 Cadrage — cahier des charges et spécification technique
- [x] J2 Setup — repo, uv, pre-commit, CI
- [x] J3 Ingestion
- [x] J4 Modélisation dbt
- [x] J5 Dashboard
- [ ] J6 Automatisation et mise en ligne
- [ ] J7 Finalisation

## Données

Données fournies par [football-data.org](https://www.football-data.org/) (offre gratuite).
