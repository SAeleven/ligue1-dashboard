from typing import Any

import httpx
import pytest
import respx

from ligue1.client import ApiError, FootballDataClient
from tests.conftest import FakeTime, load_fixture

BASE = "https://api.football-data.org/v4"
MATCHES_URL = f"{BASE}/competitions/FL1/matches"


def make_client(fake_time: FakeTime, **kwargs: Any) -> FootballDataClient:
    return FootballDataClient(
        "secret-token", sleep=fake_time.sleep, clock=fake_time.clock, **kwargs
    )


@respx.mock
def test_fetch_sends_token_and_season(fake_time: FakeTime) -> None:
    route = respx.get(MATCHES_URL).respond(json=load_fixture("matches"))
    with make_client(fake_time) as client:
        payload = client.fetch("matches", 2026)

    request = route.calls.last.request
    assert request.headers["X-Auth-Token"] == "secret-token"
    assert request.url.params["season"] == "2026"
    assert len(payload["matches"]) == 2


@respx.mock
def test_scorers_requests_a_limit(fake_time: FakeTime) -> None:
    route = respx.get(f"{BASE}/competitions/FL1/scorers").respond(json=load_fixture("scorers"))
    with make_client(fake_time) as client:
        client.fetch("scorers", 2026)
    assert route.calls.last.request.url.params["limit"] == "50"


@respx.mock
def test_waits_min_interval_between_calls(fake_time: FakeTime) -> None:
    respx.get(MATCHES_URL).respond(json={})
    with make_client(fake_time, min_interval=6.0) as client:
        client.get("/competitions/FL1/matches")
        fake_time.now += 2.0  # 2 s se sont écoulées depuis l'appel précédent
        client.get("/competitions/FL1/matches")
    assert fake_time.sleeps == [pytest.approx(4.0)]


@respx.mock
def test_no_wait_when_interval_already_elapsed(fake_time: FakeTime) -> None:
    respx.get(MATCHES_URL).respond(json={})
    with make_client(fake_time, min_interval=6.0) as client:
        client.get("/competitions/FL1/matches")
        fake_time.now += 10.0
        client.get("/competitions/FL1/matches")
    assert fake_time.sleeps == []


@respx.mock
@pytest.mark.parametrize("status", [429, 500, 503])
def test_retries_transient_errors_then_succeeds(fake_time: FakeTime, status: int) -> None:
    route = respx.get(MATCHES_URL)
    route.side_effect = [httpx.Response(status), httpx.Response(200, json={"ok": True})]
    with make_client(fake_time, min_interval=0.0, backoff_base=2.0) as client:
        assert client.get("/competitions/FL1/matches") == {"ok": True}
    assert route.call_count == 2
    assert fake_time.sleeps == [2.0]


@respx.mock
def test_backoff_is_exponential_and_gives_up(fake_time: FakeTime) -> None:
    route = respx.get(MATCHES_URL).respond(503)
    with (
        make_client(fake_time, min_interval=0.0, backoff_base=2.0, max_attempts=3) as client,
        pytest.raises(ApiError) as exc_info,
    ):
        client.get("/competitions/FL1/matches")
    assert route.call_count == 3
    assert fake_time.sleeps == [2.0, 4.0]
    assert exc_info.value.status_code == 503


@respx.mock
def test_429_honours_reset_header(fake_time: FakeTime) -> None:
    route = respx.get(MATCHES_URL)
    route.side_effect = [
        httpx.Response(429, headers={"X-RequestCounter-Reset": "23"}),
        httpx.Response(200, json={}),
    ]
    with make_client(fake_time, min_interval=0.0) as client:
        client.get("/competitions/FL1/matches")
    assert fake_time.sleeps == [23.0]


@respx.mock
def test_retries_network_errors(fake_time: FakeTime) -> None:
    route = respx.get(MATCHES_URL)
    route.side_effect = [httpx.ConnectError("boom"), httpx.Response(200, json={})]
    with make_client(fake_time, min_interval=0.0) as client:
        client.get("/competitions/FL1/matches")
    assert route.call_count == 2


@respx.mock
@pytest.mark.parametrize("status", [400, 403, 404])
def test_client_errors_are_not_retried(fake_time: FakeTime, status: int) -> None:
    route = respx.get(MATCHES_URL).respond(status, text="nope")
    with make_client(fake_time) as client, pytest.raises(ApiError) as exc_info:
        client.get("/competitions/FL1/matches")
    assert route.call_count == 1
    assert exc_info.value.status_code == status


@respx.mock
def test_non_object_json_is_rejected(fake_time: FakeTime) -> None:
    respx.get(MATCHES_URL).respond(json=[1, 2, 3])
    with make_client(fake_time) as client, pytest.raises(ApiError):
        client.get("/competitions/FL1/matches")


def test_token_not_in_error_message(fake_time: FakeTime) -> None:
    with respx.mock:
        respx.get(MATCHES_URL).respond(401, text="invalid token")
        with make_client(fake_time) as client, pytest.raises(ApiError) as exc_info:
            client.get("/competitions/FL1/matches")
    assert "secret-token" not in str(exc_info.value)
