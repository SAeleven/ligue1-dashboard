"""Extraction : API football-data.org → couche raw (fichiers JSON).

Usage :
    python -m ligue1.extract --season 2026
    python -m ligue1.extract --season 2026 --scorers

Chaque réponse est écrite dans
`data/raw/{endpoint}/season={YYYY}/date={YYYY-MM-DD}/{endpoint}.json`.
Toutes les réponses sont récupérées et validées avant la moindre écriture :
un run en échec ne laisse jamais de snapshot partiel. Relancer le même jour
réécrit les fichiers du jour (idempotence).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from ligue1.client import ApiError, Endpoint, FootballDataClient, FootballSource
from ligue1.config import get_settings
from ligue1.models import validate_payload

logger = logging.getLogger(__name__)

CORE_ENDPOINTS: tuple[Endpoint, ...] = ("matches", "standings", "teams")
OPTIONAL_ENDPOINTS: tuple[Endpoint, ...] = ("scorers",)


def current_season(today: date) -> int:
    """Année de début de la saison en cours (la Ligue 1 démarre en août)."""
    return today.year if today.month >= 7 else today.year - 1


def raw_path(data_dir: Path, endpoint: Endpoint, season: int, extracted_on: date) -> Path:
    """Chemin d'un fichier de la couche raw."""
    return (
        data_dir
        / "raw"
        / endpoint
        / f"season={season}"
        / f"date={extracted_on.isoformat()}"
        / f"{endpoint}.json"
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Écrit un JSON de façon atomique (fichier temporaire puis renommage)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def extract(
    source: FootballSource,
    season: int,
    data_dir: Path,
    extracted_on: date,
    *,
    include_optional: bool = False,
) -> list[Path]:
    """Récupère, valide puis écrit les endpoints ; renvoie les fichiers écrits.

    Un endpoint optionnel refusé par l'API (403, hors offre gratuite) est ignoré
    avec un avertissement ; toute autre erreur interrompt le run.
    """
    endpoints = CORE_ENDPOINTS + (OPTIONAL_ENDPOINTS if include_optional else ())
    payloads: dict[Endpoint, dict[str, Any]] = {}

    for endpoint in endpoints:
        try:
            payload = source.fetch(endpoint, season)
        except ApiError as exc:
            if endpoint in OPTIONAL_ENDPOINTS and exc.status_code == 403:
                logger.warning("%s : non disponible avec ce token (HTTP 403), ignoré", endpoint)
                continue
            raise
        validate_payload(endpoint, payload)
        payloads[endpoint] = payload
        logger.info("%s : réponse valide", endpoint)

    written = []
    for endpoint, payload in payloads.items():
        path = raw_path(data_dir, endpoint, season, extracted_on)
        write_json(path, payload)
        written.append(path)
        logger.info("%s : écrit dans %s", endpoint, path)
    return written


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(description="Extrait les données Ligue 1 vers data/raw.")
    parser.add_argument(
        "--season",
        type=int,
        default=None,
        help="Année de début de saison (défaut : saison en cours).",
    )
    parser.add_argument(
        "--scorers",
        action="store_true",
        help="Tente aussi l'endpoint des buteurs (ignoré s'il n'est pas disponible).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée CLI."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = parse_args(argv)
    settings = get_settings()
    today = datetime.now(UTC).date()
    season = args.season if args.season is not None else current_season(today)

    with FootballDataClient(
        token=settings.football_data_token.get_secret_value(),
        base_url=settings.football_data_base_url,
        competition=settings.competition_code,
    ) as client:
        written = extract(client, season, settings.data_dir, today, include_optional=args.scorers)

    logger.info("Extraction terminée : %d fichier(s), saison %d", len(written), season)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
