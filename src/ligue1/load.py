"""Chargement : couche raw (fichiers JSON) → DuckDB, schéma `raw`.

Usage :
    python -m ligue1.load

Chaque endpoint devient une table `raw.<endpoint>` avec une ligne par fichier :

| colonne        | contenu                                              |
| -------------- | ---------------------------------------------------- |
| `season`       | saison, lue dans le chemin (`season=YYYY`)            |
| `extracted_on` | date du snapshot, lue dans le chemin (`date=…`)       |
| `source_file`  | chemin du fichier                                    |
| `payload`      | réponse de l'API, telle quelle, en type JSON         |
| `loaded_at`    | horodatage du chargement                              |

Le JSON reste intact : tout le dépliage se fait en SQL dans dbt (staging). Les
tables sont reconstruites intégralement depuis les fichiers à chaque run, dans une
seule transaction : relancer le chargement ne crée jamais de doublon.
"""

from __future__ import annotations

import logging
from pathlib import Path

import duckdb

from ligue1.client import Endpoint
from ligue1.config import get_settings

logger = logging.getLogger(__name__)

ENDPOINTS: tuple[Endpoint, ...] = ("matches", "standings", "teams", "scorers")

CREATE_TABLE = """
create or replace table raw.{table} (
    season integer not null,
    extracted_on date not null,
    source_file varchar not null,
    payload json not null,
    loaded_at timestamp with time zone not null
)
"""

INSERT_FILES = r"""
insert into raw.{table}
select
    regexp_extract(filename, 'season=(\d{4})', 1)::integer,
    regexp_extract(filename, 'date=(\d{4}-\d{2}-\d{2})', 1)::date,
    filename,
    content::json,
    current_timestamp
from read_text({files})
"""


def raw_files(data_dir: Path, endpoint: Endpoint) -> list[Path]:
    """Fichiers de la couche raw d'un endpoint, triés par saison puis date."""
    return sorted((data_dir / "raw" / endpoint).glob("season=*/date=*/*.json"))


def _sql_list(paths: list[Path]) -> str:
    """Liste SQL de chemins littéraux (barres obliques, apostrophes échappées)."""
    quoted = ("'" + p.as_posix().replace("'", "''") + "'" for p in paths)
    return "[" + ", ".join(quoted) + "]"


def load(data_dir: Path, db_path: Path) -> dict[Endpoint, int]:
    """Reconstruit les tables `raw.*` ; renvoie le nombre de snapshots par endpoint."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[Endpoint, int] = {}
    with duckdb.connect(str(db_path)) as con:
        con.begin()
        con.execute("create schema if not exists raw")
        for endpoint in ENDPOINTS:
            con.execute(CREATE_TABLE.format(table=endpoint))
            files = raw_files(data_dir, endpoint)
            if files:
                con.execute(INSERT_FILES.format(table=endpoint, files=_sql_list(files)))
            counts[endpoint] = len(files)
        con.commit()

    for endpoint, count in counts.items():
        logger.info("raw.%s : %d snapshot(s)", endpoint, count)
    return counts


def main() -> int:
    """Point d'entrée CLI."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    counts = load(settings.data_dir, settings.duckdb_path)
    if counts["matches"] == 0:
        logger.error(
            "Aucun snapshot de matchs dans %s : lance d'abord l'extraction.", settings.data_dir
        )
        return 1
    logger.info("Chargement terminé dans %s", settings.duckdb_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
