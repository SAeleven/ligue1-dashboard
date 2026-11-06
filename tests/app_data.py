"""Petits jeux de marts construits à la main pour tester la logique du dashboard."""

from datetime import UTC, date, datetime

import pandas as pd

PSG, OM, OL = 524, 516, 523


def teams() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "team_id": [PSG, OM, OL],
            "season": 2026,
            "team_name": ["Paris Saint-Germain FC", "Olympique de Marseille", "Olympique Lyonnais"],
            "short_name": ["PSG", "Marseille", "Lyon"],
            "tla": ["PSG", "MAR", "OL"],
            "crest_url": ["psg.png", "om.png", "ol.png"],
        }
    )


def matches() -> pd.DataFrame:
    def utc(day: int, hour: int) -> datetime:
        return datetime(2026, 8, day, hour, tzinfo=UTC)

    return pd.DataFrame(
        {
            "match_id": [1, 2, 3, 4],
            "season": 2026,
            "matchday": [1, 1, 2, 2],
            "kickoff_at": pd.to_datetime([utc(15, 19), utc(16, 15), utc(22, 19), utc(23, 15)]),
            "status": ["FINISHED", "FINISHED", "TIMED", "POSTPONED"],
            "is_played": [True, True, False, False],
            "home_team_id": [PSG, OL, OM, OL],
            "home_team": ["PSG", "Lyon", "Marseille", "Lyon"],
            "home_crest_url": ["psg.png", "ol.png", "om.png", "ol.png"],
            "away_team_id": [OM, PSG, PSG, OM],
            "away_team": ["Marseille", "PSG", "PSG", "Marseille"],
            "away_crest_url": ["om.png", "psg.png", "psg.png", "om.png"],
            "home_goals": [3.0, 1.0, None, None],
            "away_goals": [0.0, 1.0, None, None],
            "outcome": ["home", "draw", None, None],
        }
    )


def standings() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "team_id": [OM, PSG, OL],
            "season": 2026,
            "last_matchday": 1,
            "position": [3, 1, 2],
            "short_name": ["Marseille", "PSG", "Lyon"],
            "tla": ["MAR", "PSG", "OL"],
            "crest_url": ["om.png", "psg.png", "ol.png"],
            "played": [1, 2, 1],
            "won": [0, 1, 0],
            "drawn": [0, 1, 1],
            "lost": [1, 0, 0],
            "goals_for": [0, 4, 1],
            "goals_against": [3, 1, 1],
            "goal_difference": [-3, 3, 0],
            "points": [0, 4, 1],
            "form": ["L", "WD", "D"],
            "zone": ["Ligue des champions", "Ligue des champions", "Ligue des champions"],
        }
    )


def history() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "season": 2026,
            "matchday": [1, 1, 1],
            "team_id": [PSG, OL, OM],
            "short_name": ["PSG", "Lyon", "Marseille"],
            "tla": ["PSG", "OL", "MAR"],
            "position": [1, 2, 3],
            "points": [4, 1, 0],
        }
    )


def profiles() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "team_id": [PSG, OM],
            "season": 2026,
            "short_name": ["PSG", "Marseille"],
            "played": [2, 1],
            "home_won": [1, 0],
            "home_drawn": [0, 0],
            "home_lost": [0, 0],
            "away_won": [0, 0],
            "away_drawn": [1, 0],
            "away_lost": [0, 1],
            "goals_for_per_match": [2.0, 0.0],
            "goals_against_per_match": [0.5, 3.0],
        }
    )


def scorers() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "player_id": [10, 11, 12],
            "season": 2026,
            "rank": [1, 2, 2],
            "player_name": ["Alpha", "Bravo", "Charlie"],
            "team_id": [PSG, OM, PSG],
            "team": ["PSG", "Marseille", "PSG"],
            "crest_url": ["psg.png", "om.png", "psg.png"],
            "goals": [3, 2, 2],
            "assists": [1, None, 0],
            "penalties": [0, 1, None],
        }
    )


def overview(season: int = 2026) -> dict[str, object]:
    return {
        "season": season,
        "matches_played": 2,
        "goals_per_match": 2.5,
        "home_win_pct": 50.0,
        "draw_pct": 50.0,
        "away_win_pct": 0.0,
        "last_played_matchday": 1,
        "next_matchday": 2,
        "biggest_win_match_id": 1,
        "highest_scoring_match_id": 1,
        "data_as_of": pd.Timestamp(date(2026, 8, 17)),
    }
