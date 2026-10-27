import json
from datetime import date
from pathlib import Path

import duckdb
import pytest

from ligue1.load import load, raw_files
from tests.seed import FIXTURES, seed_raw


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "warehouse" / "ligue1.duckdb"


def query(db_path: Path, sql: str) -> list[tuple[object, ...]]:
    with duckdb.connect(str(db_path), read_only=True) as con:
        return con.execute(sql).fetchall()


def test_load_creates_one_row_per_snapshot(tmp_path: Path, db_path: Path) -> None:
    seed_raw(tmp_path)
    counts = load(tmp_path, db_path)

    assert counts == {"matches": 1, "standings": 1, "teams": 1, "scorers": 1}
    rows = query(db_path, "select season, extracted_on, source_file from raw.matches")
    assert rows == [
        (2026, date(2026, 8, 16), raw_files(tmp_path, "matches")[0].as_posix()),
    ]


def test_payload_is_stored_untouched(tmp_path: Path, db_path: Path) -> None:
    seed_raw(tmp_path)
    load(tmp_path, db_path)
    ((payload,),) = query(db_path, "select payload from raw.teams")
    original = json.loads((FIXTURES / "teams.json").read_text(encoding="utf-8"))
    assert json.loads(str(payload)) == original


def test_json_is_queryable(tmp_path: Path, db_path: Path) -> None:
    seed_raw(tmp_path)
    load(tmp_path, db_path)
    rows = query(
        db_path,
        "select json_array_length(payload, '$.matches') from raw.matches",
    )
    assert rows == [(2,)]


def test_reload_is_idempotent(tmp_path: Path, db_path: Path) -> None:
    seed_raw(tmp_path)
    load(tmp_path, db_path)
    load(tmp_path, db_path)
    assert query(db_path, "select count(*) from raw.matches") == [(1,)]


def test_snapshots_accumulate_across_days(tmp_path: Path, db_path: Path) -> None:
    seed_raw(tmp_path, day=date(2026, 8, 16))
    seed_raw(tmp_path, day=date(2026, 8, 17))
    load(tmp_path, db_path)
    rows = query(db_path, "select extracted_on from raw.standings order by 1")
    assert rows == [(date(2026, 8, 16),), (date(2026, 8, 17),)]


def test_missing_endpoint_gives_empty_table(tmp_path: Path, db_path: Path) -> None:
    seed_raw(tmp_path)
    for path in raw_files(tmp_path, "scorers"):
        path.unlink()
    counts = load(tmp_path, db_path)
    assert counts["scorers"] == 0
    assert query(db_path, "select count(*) from raw.scorers") == [(0,)]
