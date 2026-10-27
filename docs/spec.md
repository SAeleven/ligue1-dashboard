# Ligue 1 Dashboard — Spécification technique

27 octobre 2026 · Noah

## 1. Vue d'ensemble

Chaque jour à 6 h (heure de Paris), un workflow GitHub Actions exécute quatre étapes :

1. **Extract** : un script Python appelle l'API football-data.org et écrit les réponses brutes en JSON (couche raw).
2. **Load** : les JSON sont chargés tels quels dans DuckDB (schéma `raw`).
3. **Transform** : dbt construit les couches `staging`, `intermediate` et `marts`, puis exécute les tests.
4. **Publish** : les marts sont exportés en Parquet et poussés sur le repo ; l'app Streamlit les relit.

Chaque étape se lance aussi seule en local via une commande `make`.

## 2. Source de données

| Endpoint | Données | Usage | Offre gratuite |
| --- | --- | --- | --- |
| `GET /v4/competitions/FL1/matches` | Tous les matchs de la saison : journée, date, statut, équipes, score final et mi-temps | F2, F3, F4 et recalcul du classement | Oui |
| `GET /v4/competitions/FL1/standings` | Classement actuel (général, domicile, extérieur), forme | Contrôle du classement recalculé | Oui |
| `GET /v4/competitions/FL1/teams` | Équipes : id, nom, nom court, sigle, logo | Dimension équipe | Oui |
| `GET /v4/competitions/FL1/scorers` | Meilleurs buteurs | F5 | Oui (vérifié le 27/10/2026) |

- URL de base `https://api.football-data.org/v4`, authentification par l'en-tête `X-Auth-Token`.
- Code de la Ligue 1 : `FL1`. Saison en paramètre `season=YYYY` (année de début).
- Buteurs par match, compositions et cartons relèvent de l'offre payante.

Le classement par journée n'est pas fourni en gratuit pour les journées passées : il est **recalculé en SQL** à partir des matchs, et comparé au classement officiel par un test dbt.

## 3. Ingestion

| Module | Rôle |
| --- | --- |
| `client.py` | Client `httpx` : en-tête d'auth, timeout de 30 s, 3 tentatives avec backoff exponentiel sur 429 et 5xx, au moins 6 s entre deux appels |
| `models.py` | Modèles Pydantic des réponses : un changement de format de l'API fait échouer le run au lieu de corrompre les données |
| `extract.py` | CLI `python -m ligue1.extract --season 2026` : appelle les endpoints et écrit la couche raw |

**Couche raw.** Une réponse par fichier, jamais modifiée après écriture :

```
data/raw/{endpoint}/season={YYYY}/date={YYYY-MM-DD}/{endpoint}.json
```

**Load.** `load.py` lit tous les JSON avec `read_json` de DuckDB vers des tables `raw.<endpoint>`, en ajoutant `_extracted_at` et `_source_file`.

**Idempotence.** Un run le même jour réécrit le fichier de la date du jour ; le load reconstruit les tables raw depuis les fichiers.

**Secrets.** `FOOTBALL_DATA_TOKEN` est lu depuis l'environnement : `.env` en local, secret GitHub en CI.

## 4. Modèle de données

| Couche | Modèle | Grain | Contenu |
| --- | --- | --- | --- |
| staging | `stg_matches` | match | Dernier snapshot de chaque match, typé et renommé |
| staging | `stg_teams` | équipe | Id, nom, nom court, sigle, URL du logo |
| staging | `stg_standings` | équipe × type | Classement officiel du dernier snapshot |
| intermediate | `int_team_matches` | équipe × match | Domicile/extérieur, buts pour/contre, résultat V/N/D, points |
| intermediate | `int_standings_by_matchday` | équipe × journée | Cumuls et rang via fonctions de fenêtre |
| marts | `dim_teams` | équipe | Dimension équipe |
| marts | `fct_matches` | match | Matchs joués et à venir (F4) |
| marts | `mart_standings_current` | équipe | Classement + forme 5 matchs + zone (F1) |
| marts | `mart_standings_history` | équipe × journée | Rang et points cumulés (F2) |
| marts | `mart_team_profile` | équipe | Bilans dom./ext., moyennes de buts, séries (F3) |
| marts | `mart_league_overview` | saison | Moyennes de la ligue et faits marquants (F3, F4) |

Conventions : snake_case, préfixe par couche, une clé `*_id` par entité ; staging et intermediate en vues, marts en tables.

## 5. Dashboard

Une page Streamlit qui lit les marts en Parquet via DuckDB, sans accès à l'API. F1 à gauche, F2–F4 empilés à droite. Sélection via `st.dataframe(on_select=…)`, état dans `st.session_state`, graphiques Plotly, lecture mise en cache avec `st.cache_data`. Code : `app/main.py`, `app/data.py`, `app/blocks/{standings,evolution,profile,matches}.py`.

## 6. Orchestration et déploiement

Les données vivent sur une branche Git orpheline `data`, séparée du code.

| Workflow | Déclencheur | Étapes |
| --- | --- | --- |
| `ci.yml` | Push et pull request | ruff, mypy, pytest, `dbt build` sur fixtures |
| `pipeline.yml` | Cron `0 5 * * *` (UTC) + manuel | extract → load → `dbt build` → export Parquet → commit sur `data` |

Streamlit Community Cloud déploie depuis `main` et lit les Parquet de `data` par HTTPS (`httpfs`). Un test dbt en échec arrête le run avant l'export.

## 7. Conventions

| Domaine | Convention |
| --- | --- |
| Python | 3.12, mypy strict, ruff, docstrings sur les fonctions publiques |
| SQL | Mots-clés en minuscules, CTE, un modèle par fichier |
| Git | Une branche par jalon (`feat/ingestion`…), Conventional Commits, merge sur `main` par PR |
| Décisions | ADR courts dans `docs/adr/` |
| Config | Aucun chemin ni token en dur ; variables dans `.env.example` |

## 8. Tests et qualité

| Niveau | Outil | Vérifié |
| --- | --- | --- |
| Ingestion | pytest + `respx` | Retry 429/5xx, délai entre appels, rejet d'une réponse mal formée, chemins raw |
| Génériques | tests dbt | `unique`, `not_null`, `relationships`, `accepted_values` |
| Métier | tests dbt singuliers | Points = 3V + N ; 2 lignes par match ; buts pour = buts contre ; classement recalculé = officiel |
| Logique SQL | dbt unit tests | Rang et départage |
| Dashboard | test de fumée pytest | L'app démarre, chaque bloc se charge |

## 9. Questions ouvertes

- [x] Endpoint `scorers` accessible en gratuit ? **Oui** (test réel du 27/10/2026, HTTP 200) : F5 entre dans le périmètre
- [ ] Règles de départage de la Ligue 1 (règlement LFP, avant J4)
- [ ] Volume réel des snapshots `matches` compressés — mesure du 27/10/2026 : ~480 Ko brut par snapshot, soit ~150 Mo brut par saison ; à confirmer compressé en J6
- [ ] Lecture HTTPS des Parquet depuis Streamlit Community Cloud (J6)
