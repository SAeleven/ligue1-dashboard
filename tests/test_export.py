from pathlib import Path

import duckdb
import pytest

from ligue1.export import export


def make_db(path: Path) -> None:
    with duckdb.connect(str(path)) as con:
        con.execute("create schema marts")
        con.execute("create table marts.dim_teams as select 524 as team_id, 'PSG' as tla")
        con.execute("create table marts.fct_matches as select 1 as match_id")
        con.execute("create view marts.not_exported as select 1 as x")
        con.execute("create schema staging")
        con.execute("create table staging.ignored as select 1 as x")


def test_export_writes_one_parquet_per_mart_table(tmp_path: Path) -> None:
    db = tmp_path / "ligue1.duckdb"
    make_db(db)
    written = export(db, tmp_path / "marts")

    assert [p.name for p in written] == ["dim_teams.parquet", "fct_matches.parquet"]
    rows = duckdb.sql(f"select * from read_parquet('{written[0].as_posix()}')").fetchall()
    assert rows == [(524, "PSG")]


def test_export_overwrites_previous_files(tmp_path: Path) -> None:
    db = tmp_path / "ligue1.duckdb"
    make_db(db)
    export(db, tmp_path / "marts")
    written = export(db, tmp_path / "marts")
    assert len(written) == 2


def test_export_requires_database(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        export(tmp_path / "absente.duckdb", tmp_path / "marts")


def test_export_requires_marts(tmp_path: Path) -> None:
    db = tmp_path / "vide.duckdb"
    duckdb.connect(str(db)).close()
    with pytest.raises(RuntimeError):
        export(db, tmp_path / "marts")
