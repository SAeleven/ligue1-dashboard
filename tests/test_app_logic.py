from datetime import datetime

import pandas as pd
import pytest
from app import data, state
from app import format as fmt
from app.blocks import evolution, matches, profile, scorers, standings

from tests import app_data
from tests.app_data import OL, OM, PSG

# --- format -------------------------------------------------------------------


def test_form_icons() -> None:
    assert fmt.form_icons("WDL") == "🟢⚪🔴"
    assert fmt.form_icons(None) == ""


@pytest.mark.parametrize(
    ("result", "length", "expected"),
    [("W", 3, "3 victoires"), ("D", 1, "1 nul"), ("L", 2, "2 défaites"), (None, 0, "—")],
)
def test_streak_text(result: str | None, length: int, expected: str) -> None:
    assert fmt.streak_text(result, length) == expected


def test_season_label() -> None:
    assert fmt.season_label(2026) == "2026-27"
    assert fmt.season_label(2099) == "2099-00"


def test_score_label() -> None:
    assert fmt.score_label(2.0, 1.0, "FINISHED") == "2 - 1"
    assert fmt.score_label(float("nan"), None, "TIMED") == "–"
    assert fmt.score_label(None, None, "POSTPONED") == "Reporté"


def test_kickoff_label() -> None:
    assert fmt.kickoff_label(datetime(2026, 11, 8, 21, 0)) == "dim. 08/11 · 21:00"


# --- state ----------------------------------------------------------------------


def test_team_id_from_tla() -> None:
    teams = app_data.teams()
    assert state.team_id_from_tla(teams, "psg") == PSG
    assert state.team_id_from_tla(teams, "XXX") is None
    assert state.team_id_from_tla(teams, None) is None


# --- data -----------------------------------------------------------------------


def test_build_marts_keeps_latest_season_and_local_time() -> None:
    old = app_data.overview(season=2025)
    tables = {
        "mart_league_overview": pd.DataFrame([old, app_data.overview()]),
        "dim_teams": app_data.teams(),
        "fct_matches": app_data.matches(),
        "mart_standings_current": app_data.standings(),
        "mart_standings_history": app_data.history(),
        "mart_team_profile": app_data.profiles(),
        "mart_top_scorers": app_data.scorers(),
    }
    marts = data.build_marts(tables)
    assert marts.season == 2026
    assert marts.standings["position"].tolist() == [1, 2, 3]
    first_kickoff = marts.matches["kickoff_at"].iloc[0]
    assert str(first_kickoff.tz) == "Europe/Paris"
    assert first_kickoff.hour == 21  # 19:00 UTC = 21:00 à Paris en août


def test_build_marts_requires_overview() -> None:
    with pytest.raises(data.DataUnavailableError):
        data.build_marts({"mart_league_overview": pd.DataFrame(columns=["season"])})


# --- F1 classement ----------------------------------------------------------------


def test_standings_table_is_sorted_with_display_columns() -> None:
    table = standings.standings_table(app_data.standings())
    assert table["Équipe"].tolist() == ["PSG", "Lyon", "Marseille"]
    assert table["tla"].tolist() == ["PSG", "OL", "MAR"]
    assert table.loc[0, "Forme"] == "🟢⚪"
    assert table.loc[0, "Zone"] == "🟦"


# --- F2 évolution ------------------------------------------------------------------


def test_evolution_highlights_selected_team_last() -> None:
    fig = evolution.evolution_figure(app_data.history(), app_data.standings(), OM, "position")
    assert len(fig.data) == 3
    assert fig.data[-1].name == "Marseille"
    assert fig.data[-1].line.color == fmt.ACCENT
    assert all(trace.line.color == fmt.CONTEXT for trace in fig.data[:-1])
    assert list(fig.layout.yaxis.range) == [3.5, 0.5]  # rang 1 en haut


def test_evolution_without_selection_is_all_context() -> None:
    fig = evolution.evolution_figure(app_data.history(), app_data.standings(), None, "points")
    assert {trace.line.color for trace in fig.data} == {fmt.CONTEXT}
    assert fig.layout.yaxis.title.text == "Points"


# --- F3 profil ---------------------------------------------------------------------


def test_home_away_records() -> None:
    psg = app_data.profiles().iloc[0]
    records = profile.home_away_records(psg)
    assert len(records) == 6
    home_wins = records[(records["venue"] == "Domicile") & (records["result"] == "Victoires")]
    assert home_wins["count"].item() == 1


def test_league_goals_per_team_match() -> None:
    assert profile.league_goals_per_team_match(pd.Series(app_data.overview())) == 1.25
    assert profile.league_goals_per_team_match(pd.Series({"goals_per_match": None})) is None


def test_attack_defense_highlights_selection() -> None:
    fig = profile.attack_defense_figure(app_data.profiles(), PSG)
    assert len(fig.data) == 2
    assert list(fig.data[-1].customdata) == ["PSG"]


# --- F4 matchs ---------------------------------------------------------------------


def test_team_result() -> None:
    m = app_data.matches()
    assert matches.team_result(m.iloc[0], PSG) == "W"
    assert matches.team_result(m.iloc[0], OM) == "L"
    assert matches.team_result(m.iloc[1], PSG) == "D"
    assert matches.team_result(m.iloc[2], PSG) is None


def test_team_fixtures_split_recent_and_upcoming() -> None:
    recent, upcoming = matches.team_fixtures(app_data.matches(), OM)
    assert recent["match_id"].tolist() == [1]
    assert upcoming["match_id"].tolist() == [3, 4]  # le match reporté reste à venir


def test_fixtures_table_with_team_results() -> None:
    m = app_data.matches()
    m["kickoff_at"] = data.to_local_time(m["kickoff_at"])
    table = matches.fixtures_table(m[m["is_played"]], PSG)
    assert table["Rés."].tolist() == ["🟢 V", "⚪ N"]
    assert table["Score"].tolist() == ["3 - 0", "1 - 1"]
    assert table.loc[0, "Date"] == "sam. 15/08 · 21:00"


def test_match_summary() -> None:
    m = app_data.matches()
    assert matches.match_summary(m, 1) == "PSG 3 - 0 Marseille (J1)"
    assert matches.match_summary(m, None) is None
    assert matches.match_summary(m, 999) is None


# --- F5 buteurs --------------------------------------------------------------------


def test_top_scorers_for_league_and_team() -> None:
    league = scorers.top_scorers(app_data.scorers())
    assert league["Joueur"].tolist() == ["Alpha", "Bravo", "Charlie"]
    psg = scorers.top_scorers(app_data.scorers(), PSG)
    assert psg["Joueur"].tolist() == ["Alpha", "Charlie"]
    assert scorers.top_scorers(app_data.scorers(), OL).empty
