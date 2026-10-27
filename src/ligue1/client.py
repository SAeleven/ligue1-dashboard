"""Client HTTP de l'API football-data.org v4.

Le client ne contient aucune logique métier : il envoie les requêtes, respecte le
rate limit de l'offre gratuite (10 appels par minute) et relance les erreurs
transitoires. Le reste du pipeline ne dépend que du protocole `FootballSource`,
ce qui permet de changer de fournisseur sans toucher à l'extraction.
"""

from __future__ import annotations

import contextlib
import logging
import time
from collections.abc import Callable
from types import TracebackType
from typing import Any, Literal, Protocol, Self

import httpx

logger = logging.getLogger(__name__)

Endpoint = Literal["matches", "standings", "teams", "scorers"]

RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
MAX_RETRY_DELAY = 60.0


class ApiError(Exception):
    """Erreur définitive renvoyée par l'API (ou réseau après épuisement des tentatives)."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Conserve le code HTTP pour que l'appelant puisse décider quoi faire."""
        super().__init__(message)
        self.status_code = status_code


class FootballSource(Protocol):
    """Interface minimale d'une source de données football."""

    def fetch(self, endpoint: Endpoint, season: int) -> dict[str, Any]:
        """Renvoie la réponse brute (JSON décodé) d'un endpoint pour une saison."""
        ...


class FootballDataClient:
    """Client football-data.org : authentification, throttling, retries."""

    def __init__(
        self,
        token: str,
        base_url: str = "https://api.football-data.org/v4",
        competition: str = "FL1",
        *,
        min_interval: float = 6.0,
        max_attempts: int = 3,
        backoff_base: float = 2.0,
        timeout: float = 30.0,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Crée le client.

        Args:
            token: token API, envoyé dans l'en-tête `X-Auth-Token`.
            base_url: URL de base de l'API.
            competition: code de la compétition (`FL1` pour la Ligue 1).
            min_interval: délai minimum en secondes entre deux appels.
            max_attempts: nombre total de tentatives par requête.
            backoff_base: délai de la première relance, doublé à chaque tentative.
            timeout: timeout HTTP en secondes.
            sleep: fonction d'attente (injectable pour les tests).
            clock: horloge monotone (injectable pour les tests).

        """
        if max_attempts < 1:
            raise ValueError("max_attempts doit être >= 1")
        self.competition = competition
        self._min_interval = min_interval
        self._max_attempts = max_attempts
        self._backoff_base = backoff_base
        self._sleep = sleep
        self._clock = clock
        self._last_call: float | None = None
        self._http = httpx.Client(
            base_url=base_url,
            headers={"X-Auth-Token": token},
            timeout=timeout,
        )

    def __enter__(self) -> Self:
        """Permet `with FootballDataClient(...) as client:`."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Ferme la connexion HTTP."""
        self.close()

    def close(self) -> None:
        """Ferme la connexion HTTP."""
        self._http.close()

    def fetch(self, endpoint: Endpoint, season: int) -> dict[str, Any]:
        """Appelle `/competitions/{code}/{endpoint}` pour une saison."""
        params: dict[str, str | int] = {"season": season}
        if endpoint == "scorers":
            params["limit"] = 50
        return self.get(f"/competitions/{self.competition}/{endpoint}", params)

    def get(self, path: str, params: dict[str, str | int] | None = None) -> dict[str, Any]:
        """GET avec throttling et relances sur 429, 5xx et erreurs réseau."""
        for attempt in range(1, self._max_attempts + 1):
            self._throttle()
            last_attempt = attempt == self._max_attempts
            try:
                response = self._http.get(path, params=params)
            except httpx.TransportError as exc:
                if last_attempt:
                    raise ApiError(f"GET {path} : erreur réseau ({exc})") from exc
                delay = self._backoff(attempt)
                logger.warning("GET %s : erreur réseau, relance dans %.0f s", path, delay)
                self._sleep(delay)
                continue

            if response.status_code in RETRYABLE_STATUS:
                if last_attempt:
                    raise ApiError(
                        f"GET {path} : HTTP {response.status_code} après "
                        f"{self._max_attempts} tentatives",
                        response.status_code,
                    )
                delay = self._retry_delay(response, attempt)
                logger.warning(
                    "GET %s : HTTP %s, relance dans %.0f s", path, response.status_code, delay
                )
                self._sleep(delay)
                continue

            if response.is_error:
                raise ApiError(
                    f"GET {path} : HTTP {response.status_code} — {response.text[:200]}",
                    response.status_code,
                )

            payload = response.json()
            if not isinstance(payload, dict):
                raise ApiError(f"GET {path} : réponse JSON inattendue (objet attendu)")
            return payload

        raise AssertionError("unreachable")  # pragma: no cover

    def _throttle(self) -> None:
        """Attend si l'appel précédent est trop récent."""
        if self._last_call is not None:
            wait = self._min_interval - (self._clock() - self._last_call)
            if wait > 0:
                self._sleep(wait)
        self._last_call = self._clock()

    def _backoff(self, attempt: int) -> float:
        return float(self._backoff_base * 2 ** (attempt - 1))

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        """Délai avant relance : en-têtes de l'API s'ils existent, sinon backoff."""
        delay = self._backoff(attempt)
        for header in ("Retry-After", "X-RequestCounter-Reset"):
            value = response.headers.get(header)
            if value is not None:
                with contextlib.suppress(ValueError):
                    delay = max(delay, float(value))
                break
        return min(delay, MAX_RETRY_DELAY)
