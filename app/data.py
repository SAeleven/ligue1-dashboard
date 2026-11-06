"""Accès aux données du dashboard : uniquement les marts dbt, jamais l'API (NF3).

Deux sources possibles, choisies par variable d'environnement :

- `MARTS_URL` défini : fichiers Parquet `<MARTS_URL>/<mart>.parquet`, en local ou
  par HTTPS (mise en ligne, jalon J6) ;
- sinon : la base DuckDB construite par dbt (`DUCKDB_PATH`, défaut
  `data/ligue1.duckdb`), ouverte en lecture seule.

Toutes les tables sont chargées en mémoire une fois (cache d'une heure) ; la
sélection d'une équipe filtre ensuite des DataFrames déjà chargés (NF8).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DISPLAY_TZ = "Europe/Paris"

MARTS = (
    "dim_teams",
    "fct_matches",
    "mart_standings_current",
    "mart_standings_history",
    "mart_team_profile",
    "mart_league_overview",
    "mart_top_scorers",
)


class DataUnavailableError(RuntimeError):
    """Les marts sont introuvables (pipeline pas encore lancé)."""


@dataclass(frozen=True)
class Marts:
    """Les marts d'une saison, prêts à afficher."""

    season: int
    teams: pd.DataFrame
    matches: pd.DataFrame
    standings: pd.DataFrame
    history: pd.DataFrame
    profiles: pd.DataFrame
    overview: pd.Series
    scorers: pd.DataFrame


def _read_tables(duckdb_path: str, marts_url: str | None) -> dict[str, pd.DataFrame]:
    """Lit chaque mart dans un DataFrame pandas."""
    if marts_url:
        con = duckdb.connect()
        base = marts_url.rstrip("/")
        sources = {name: f"read_parquet('{base}/{name}.parquet')" for name in MARTS}
    else:
        if not Path(duckdb_path).exists():
            raise DataUnavailableError(f"Base introuvable : {duckdb_path}")
        con = duckdb.connect(duckdb_path, read_only=True)
        sources = {name: f"marts.{name}" for name in MARTS}

    try:
        con.execute(f"set TimeZone = '{DISPLAY_TZ}'")
        return {name: con.sql(f"select * from {source}").df() for name, source in sources.items()}
    except duckdb.Error as exc:
        raise DataUnavailableError(str(exc)) from exc
    finally:
        con.close()


def to_local_time(series: pd.Series) -> pd.Series:
    """Convertit des horodatages en heure de Paris (naïfs = UTC)."""
    timestamps = pd.to_datetime(series)
    if timestamps.dt.tz is None:
        timestamps = timestamps.dt.tz_localize("UTC")
    return timestamps.dt.tz_convert(DISPLAY_TZ)


def build_marts(tables: dict[str, pd.DataFrame]) -> Marts:
    """Ne garde que la saison la plus récente et prépare les types."""
    overview = tables["mart_league_overview"]
    if overview.empty:
        raise DataUnavailableError("mart_league_overview est vide")
    season = int(overview["season"].max())

    def of_season(name: str) -> pd.DataFrame:
        df = tables[name]
        return df[df["season"] == season].reset_index(drop=True)

    matches = of_season("fct_matches")
    matches["kickoff_at"] = to_local_time(matches["kickoff_at"])

    return Marts(
        season=season,
        teams=of_season("dim_teams"),
        matches=matches.sort_values("kickoff_at").reset_index(drop=True),
        standings=of_season("mart_standings_current")
        .sort_values("position")
        .reset_index(drop=True),
        history=of_season("mart_standings_history"),
        profiles=of_season("mart_team_profile"),
        overview=of_season("mart_league_overview").iloc[0],
        scorers=of_season("mart_top_scorers").sort_values(["rank", "player_name"]),
    )


@st.cache_data(ttl=3600, show_spinner="Chargement des données…")
def load_marts(duckdb_path: str, marts_url: str | None) -> Marts:
    """Charge et met en cache les marts (une lecture par heure au plus)."""
    return build_marts(_read_tables(duckdb_path, marts_url))


def load_from_env() -> Marts:
    """Charge les marts depuis la source configurée par l'environnement."""
    return load_marts(
        os.environ.get("DUCKDB_PATH", "data/ligue1.duckdb"),
        os.environ.get("MARTS_URL") or None,
    )
