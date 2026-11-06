# ADR 0003 — Publication des données et hébergement du dashboard

- Statut : accepté
- Date : 2026-11-06

## Contexte

Le pipeline tourne chaque jour sur un runner GitHub Actions éphémère, et le dashboard
est hébergé sur Streamlit Community Cloud (NF1, NF2 : 0 €). Il faut un endroit gratuit
et durable pour :

- conserver l'historique des snapshots bruts (la couche raw s'accumule toute la saison) ;
- mettre les marts à disposition de l'app hébergée, sans la redéployer à chaque mise à jour.

## Décision

- **Branche Git orpheline `data`**, séparée du code :
  - `raw/**.json.gz` : snapshots bruts compressés en gzip déterministe (pas d'horodatage
    dans l'en-tête), environ 10 fois plus légers et sans diff Git quand rien ne change ;
  - `marts/*.parquet` : les tables marts (compression zstd), réécrites à chaque run.
- **Workflow `pipeline.yml`** : cron `0 5 * * *` (UTC) et lancement manuel. Il restaure la
  couche raw depuis `data`, puis enchaîne extract, load, `dbt build`, export et commit sur
  `data`. Un test dbt en échec arrête le run **avant** la publication : le dashboard garde
  les données de la veille et GitHub envoie un e-mail d'échec.
- **Lecture par l'app** : `MARTS_URL` pointe vers
  `https://raw.githubusercontent.com/<compte>/ligue1-dashboard/data/marts`, et DuckDB lit les
  Parquet par HTTPS (extension `httpfs`). Une nouvelle donnée ne nécessite pas de redéployer.
- **Dépendances de l'app hébergée** : `app/requirements.txt`, à côté de l'entrypoint, prend
  le pas sur `uv.lock` à la racine. L'app n'installe que streamlit, plotly, pandas et duckdb,
  sans dbt ni outils de dev. Les versions sont épinglées sur celles de `uv.lock`, et un test
  pytest vérifie qu'elles restent alignées.
- La CI exécute les tests de fumée du dashboard dans les deux modes : base DuckDB et Parquet.

## Conséquences

- Coût nul. L'historique des données est versionné et rejouable à tout moment.
- `raw.githubusercontent.com` met les fichiers en cache quelques minutes : une mise à jour
  peut apparaître avec ce délai, en plus du cache d'une heure de l'app. C'est acceptable
  pour une fraîcheur quotidienne.
- La branche `data` grossit d'environ 50 Ko par jour (raw compressé) plus les réécritures des
  marts. Si elle devenait trop lourde, il faudrait passer à un stockage objet gratuit et
  rédiger un nouvel ADR.
- L'app gratuite se met en veille après une période d'inactivité. Le premier affichage est
  alors lent, ce qui est accepté (CDC §8).
