"""Export : tables du schéma `marts` → fichiers Parquet lus par le dashboard.

Usage :
    python -m ligue1.export --out data/marts

Un fichier par mart (`<out>/<mart>.parquet`, compression zstd), réécrit à chaque
run. La liste des marts est lue dans la base : un nouveau mart dbt est exporté
sans toucher à ce module.
"""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

import duckdb

from ligue1.config import get_settings

logger = logging.getLogger(__name__)

SCHEMA = "marts"


def list_marts(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Tables du schéma `marts`, par ordre alphabétique."""
    rows = con.execute(
        "select table_name from information_schema.tables "
        "where table_schema = ? and table_type = 'BASE TABLE' order by table_name",
        [SCHEMA],
    ).fetchall()
    return [str(name) for (name,) in rows]


def export(db_path: Path, out_dir: Path) -> list[Path]:
    """Exporte chaque mart en Parquet ; renvoie les fichiers écrits."""
    if not db_path.exists():
        raise FileNotFoundError(f"Base introuvable : {db_path} (lancer load puis dbt build)")
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with duckdb.connect(str(db_path), read_only=True) as con:
        marts = list_marts(con)
        if not marts:
            raise RuntimeError(f"Aucune table dans le schéma {SCHEMA} : lancer dbt build")
        for name in marts:
            target = out_dir / f"{name}.parquet"
            path_literal = target.as_posix().replace("'", "''")
            con.execute(
                f"copy {SCHEMA}.{name} to '{path_literal}' (format parquet, compression zstd)"
            )
            written.append(target)
            logger.info("%s → %s", name, target)
    return written


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée CLI."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Exporte les marts en Parquet.")
    parser.add_argument("--out", type=Path, default=settings.data_dir / "marts")
    args = parser.parse_args(argv)
    written = export(settings.duckdb_path, args.out)
    logger.info("Export terminé : %d fichier(s) dans %s", len(written), args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
