import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from ligue1.client import ApiError, Endpoint
from ligue1.extract import current_season, extract, raw_path
from tests.conftest import load_fixture

DAY = date(2026, 10, 28)


class FakeSource:
    """Source simulée : renvoie les fixtures, ou une erreur pour certains endpoints."""

    def __init__(self, errors: dict[str, Exception] | None = None) -> None:
        self.errors = errors or {}
        self.calls: list[str] = []
        self.overrides: dict[str, dict[str, Any]] = {}

    def fetch(self, endpoint: Endpoint, season: int) -> dict[str, Any]:
        self.calls.append(endpoint)
        if endpoint in self.errors:
            raise self.errors[endpoint]
        return self.overrides.get(endpoint, load_fixture(endpoint))


def test_raw_path_layout(tmp_path: Path) -> None:
    assert raw_path(tmp_path, "matches", 2026, DAY) == (
        tmp_path / "raw/matches/season=2026/date=2026-10-28/matches.json"
    )


@pytest.mark.parametrize(
    ("today", "season"),
    [(date(2026, 10, 27), 2026), (date(2027, 3, 1), 2026), (date(2027, 7, 1), 2027)],
)
def test_current_season(today: date, season: int) -> None:
    assert current_season(today) == season


def test_extract_writes_core_endpoints(tmp_path: Path) -> None:
    source = FakeSource()
    written = extract(source, 2026, tmp_path, DAY)

    assert source.calls == ["matches", "standings", "teams"]
    assert written == [raw_path(tmp_path, e, 2026, DAY) for e in ("matches", "standings", "teams")]
    stored = json.loads(written[0].read_text(encoding="utf-8"))
    assert stored == load_fixture("matches")  # JSON stocké tel que reçu


def test_rerun_same_day_is_idempotent(tmp_path: Path) -> None:
    extract(FakeSource(), 2026, tmp_path, DAY)
    extract(FakeSource(), 2026, tmp_path, DAY)
    files = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert files == [
        "raw/matches/season=2026/date=2026-10-28/matches.json",
        "raw/standings/season=2026/date=2026-10-28/standings.json",
        "raw/teams/season=2026/date=2026-10-28/teams.json",
    ]


def test_new_day_adds_a_snapshot(tmp_path: Path) -> None:
    extract(FakeSource(), 2026, tmp_path, DAY)
    extract(FakeSource(), 2026, tmp_path, date(2026, 10, 29))
    assert len(list((tmp_path / "raw/matches/season=2026").iterdir())) == 2


def test_invalid_payload_writes_nothing(tmp_path: Path) -> None:
    source = FakeSource()
    source.overrides["teams"] = {"unexpected": "format"}
    with pytest.raises(ValidationError):
        extract(source, 2026, tmp_path, DAY)
    assert not (tmp_path / "raw").exists()


def test_api_error_on_core_endpoint_fails(tmp_path: Path) -> None:
    source = FakeSource(errors={"standings": ApiError("down", 503)})
    with pytest.raises(ApiError):
        extract(source, 2026, tmp_path, DAY)
    assert not (tmp_path / "raw").exists()


def test_scorers_included_on_demand(tmp_path: Path) -> None:
    written = extract(FakeSource(), 2026, tmp_path, DAY, include_optional=True)
    assert raw_path(tmp_path, "scorers", 2026, DAY) in written


def test_scorers_forbidden_is_skipped(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    source = FakeSource(errors={"scorers": ApiError("forbidden", 403)})
    written = extract(source, 2026, tmp_path, DAY, include_optional=True)
    assert len(written) == 3
    assert "scorers" in caplog.text


def test_scorers_other_error_still_fails(tmp_path: Path) -> None:
    source = FakeSource(errors={"scorers": ApiError("down", 503)})
    with pytest.raises(ApiError):
        extract(source, 2026, tmp_path, DAY, include_optional=True)
