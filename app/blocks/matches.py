"""F4 — Matchs : que s'est-il passé, que reste-t-il ?"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.data import Marts
from app.format import RESULT_ICONS, RESULT_LABELS, kickoff_label, score_label

UPCOMING_STATUSES = ("SCHEDULED", "TIMED", "POSTPONED")


def team_result(match: pd.Series, team_id: int) -> str | None:
    """W, D ou L du point de vue de l'équipe ; None si le match n'est pas joué."""
    if not match["is_played"]:
        return None
    if match["outcome"] == "draw":
        return "D"
    won_at_home = match["outcome"] == "home" and match["home_team_id"] == team_id
    won_away = match["outcome"] == "away" and match["away_team_id"] == team_id
    return "W" if won_at_home or won_away else "L"


def team_fixtures(
    matches: pd.DataFrame, team_id: int, n: int = 5
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(n derniers matchs joués du plus récent au plus ancien, n prochains matchs)."""
    mine = matches[(matches["home_team_id"] == team_id) | (matches["away_team_id"] == team_id)]
    recent = mine[mine["is_played"]].sort_values("kickoff_at", ascending=False).head(n)
    upcoming = mine[mine["status"].isin(UPCOMING_STATUSES)].sort_values("kickoff_at").head(n)
    return recent, upcoming


def matchday_fixtures(matches: pd.DataFrame, matchday: int) -> pd.DataFrame:
    """Matchs d'une journée, dans l'ordre chronologique."""
    return matches[matches["matchday"] == matchday].sort_values("kickoff_at")


def fixtures_table(fixtures: pd.DataFrame, team_id: int | None = None) -> pd.DataFrame:
    """Tableau d'affichage ; avec `team_id`, ajoute le résultat de l'équipe."""
    table = pd.DataFrame(
        {
            "J": fixtures["matchday"],
            "Date": fixtures["kickoff_at"].map(kickoff_label),
            "Logo dom.": fixtures["home_crest_url"],
            "Domicile": fixtures["home_team"],
            "Score": [
                score_label(home, away, status)
                for home, away, status in zip(
                    fixtures["home_goals"], fixtures["away_goals"], fixtures["status"], strict=True
                )
            ],
            "Extérieur": fixtures["away_team"],
            "Logo ext.": fixtures["away_crest_url"],
        }
    )
    if team_id is not None:
        results = [team_result(match, team_id) for _, match in fixtures.iterrows()]
        table.insert(
            0, "Rés.", [f"{RESULT_ICONS[r]} {RESULT_LABELS[r]}" if r else "" for r in results]
        )
    return table.reset_index(drop=True)


def match_summary(matches: pd.DataFrame, match_id: object) -> str | None:
    """'PSG 5 - 0 Nantes (J7)' pour un identifiant de match."""
    if pd.isna(match_id):
        return None
    found = matches[matches["match_id"] == match_id]
    if found.empty:
        return None
    m = found.iloc[0]
    score = score_label(m["home_goals"], m["away_goals"], m["status"])
    return f"{m['home_team']} {score} {m['away_team']} (J{int(m['matchday'])})"


def _show(table: pd.DataFrame, empty_message: str) -> None:
    if table.empty:
        st.caption(empty_message)
        return
    st.dataframe(
        table,
        hide_index=True,
        column_config={
            "J": st.column_config.NumberColumn(width=36),
            "Logo dom.": st.column_config.ImageColumn("", width=28),
            "Logo ext.": st.column_config.ImageColumn("", width=28),
            "Score": st.column_config.TextColumn(width="small"),
        },
    )


def _render_league(marts: Marts) -> None:
    overview, matches = marts.overview, marts.matches
    tabs: list[tuple[str, pd.DataFrame]] = []
    if not pd.isna(overview["last_played_matchday"]):
        last = int(overview["last_played_matchday"])
        tabs.append((f"Journée {last}", matchday_fixtures(matches, last)))
    if not pd.isna(overview["next_matchday"]):
        upcoming = int(overview["next_matchday"])
        tabs.append((f"Prochaine : journée {upcoming}", matchday_fixtures(matches, upcoming)))
    if tabs:
        for tab, (_, fixtures) in zip(st.tabs([label for label, _ in tabs]), tabs, strict=True):
            with tab:
                _show(fixtures_table(fixtures), "Aucun match.")

    facts = [
        ("Plus large victoire", match_summary(matches, overview["biggest_win_match_id"])),
        ("Match le plus prolifique", match_summary(matches, overview["highest_scoring_match_id"])),
    ]
    lines = [f"**{label}** : {text}" for label, text in facts if text]
    if lines:
        st.markdown("  \n".join(lines))


def _render_team(marts: Marts, team_id: int) -> None:
    recent, upcoming = team_fixtures(marts.matches, team_id)
    played_tab, next_tab = st.tabs(["Derniers résultats", "Prochains matchs"])
    with played_tab:
        _show(fixtures_table(recent, team_id), "Aucun match joué.")
    with next_tab:
        _show(fixtures_table(upcoming), "Aucun match à venir.")


def render(marts: Marts, selected_team_id: int | None) -> None:
    """Affiche le bloc Matchs."""
    st.subheader("Matchs")
    if selected_team_id is None:
        _render_league(marts)
    else:
        _render_team(marts, selected_team_id)
