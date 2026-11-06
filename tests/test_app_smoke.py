"""Tests de fumée : la page démarre et chaque bloc se charge (spec §8).

Ils s'exécutent sur la base DuckDB désignée par `DUCKDB_PATH` (défaut
`data/ligue1.duckdb`) et sont ignorés si elle n'existe pas. En CI, ils tournent
après `dbt build` sur la base construite à partir des fixtures.
"""

import os
from pathlib import Path

import duckdb
import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "main.py")
DB = Path(os.environ.get("DUCKDB_PATH", "data/ligue1.duckdb"))
needs_db = pytest.mark.skipif(not DB.exists(), reason=f"{DB} absente : lancer load puis dbt build")


def run_app(team: str | None = None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=60)
    if team is not None:
        at.query_params["equipe"] = team
    at.run()
    return at


def subheaders(at: AppTest) -> list[str]:
    return [element.value for element in at.subheader]


def any_tla() -> str:
    with duckdb.connect(str(DB), read_only=True) as con:
        row = con.execute(
            "select tla from marts.mart_standings_current order by position"
        ).fetchone()
    assert row is not None
    return str(row[0])


@needs_db
def test_league_view_renders_every_block() -> None:
    at = run_app()
    assert not at.exception
    assert at.title[0].value.startswith("Ligue 1 · saison")
    assert {"Classement", "Évolution", "Profil de la Ligue 1", "Matchs", "Buteurs"} <= set(
        subheaders(at)
    )
    assert len(at.dataframe) >= 2  # classement + buteurs (+ matchs)


@needs_db
def test_team_view_filters_blocks() -> None:
    at = run_app(any_tla())
    assert not at.exception
    assert any(title.startswith("Profil — ") for title in subheaders(at))
    assert len(at.info) == 1  # bandeau « vue filtrée »
    assert len(at.button) == 1  # retour à la vue Ligue 1


@needs_db
def test_unknown_team_falls_back_to_league_view() -> None:
    at = run_app("XXX")
    assert not at.exception
    assert "Profil de la Ligue 1" in subheaders(at)


def test_missing_data_shows_help(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("MARTS_URL", raising=False)
    monkeypatch.setenv("DUCKDB_PATH", str(tmp_path / "absente.duckdb"))
    at = run_app()
    assert not at.exception
    assert "make transform" in at.error[0].value
