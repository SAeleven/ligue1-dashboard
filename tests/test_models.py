import copy

import pytest
from pydantic import ValidationError

from ligue1.client import Endpoint
from ligue1.models import MatchesResponse, StandingsResponse, validate_payload
from tests.conftest import load_fixture


@pytest.mark.parametrize("endpoint", ["matches", "standings", "teams", "scorers"])
def test_fixtures_are_valid(endpoint: Endpoint) -> None:
    validate_payload(endpoint, load_fixture(endpoint))


def test_matches_are_parsed() -> None:
    parsed = validate_payload("matches", load_fixture("matches"))
    assert isinstance(parsed, MatchesResponse)
    played, upcoming = parsed.matches
    assert played.home_team.tla == "PSG"
    assert played.score.full_time.home == 2
    assert played.score.winner == "HOME_TEAM"
    assert upcoming.score.full_time.home is None


def test_standings_points_are_consistent() -> None:
    parsed = validate_payload("standings", load_fixture("standings"))
    assert isinstance(parsed, StandingsResponse)
    assert [s.type for s in parsed.standings] == ["TOTAL", "HOME", "AWAY"]
    for row in parsed.standings[0].table:
        assert row.points == 3 * row.won + row.draw


def test_unknown_fields_are_ignored() -> None:
    payload = load_fixture("teams")
    payload["teams"][0]["brandNewField"] = "whatever"
    validate_payload("teams", payload)


def test_missing_field_is_rejected() -> None:
    payload = copy.deepcopy(load_fixture("matches"))
    del payload["matches"][0]["score"]
    with pytest.raises(ValidationError):
        validate_payload("matches", payload)


def test_wrong_type_is_rejected() -> None:
    payload = load_fixture("standings")
    payload["standings"][0]["table"][0]["points"] = "beaucoup"
    with pytest.raises(ValidationError):
        validate_payload("standings", payload)


def test_unknown_standing_type_is_rejected() -> None:
    payload = load_fixture("standings")
    payload["standings"][0]["type"] = "GROUP"
    with pytest.raises(ValidationError):
        validate_payload("standings", payload)
