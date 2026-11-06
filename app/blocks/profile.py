"""F3 — Profil : comment joue l'équipe (ou la Ligue 1) ?"""

from __future__ import annotations

from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.data import Marts
from app.format import ACCENT, CONTEXT, DRAW, LOSS, SURFACE, WIN, streak_text

GRID = "rgba(137, 135, 129, 0.2)"
RESULTS = (("won", "Victoires", WIN), ("drawn", "Nuls", DRAW), ("lost", "Défaites", LOSS))


def league_goals_per_team_match(overview: pd.Series) -> float | None:
    """Buts marqués par une équipe et par match, en moyenne sur la ligue."""
    value = overview.get("goals_per_match")
    return None if pd.isna(value) else float(value) / 2


def home_away_records(profile: pd.Series) -> pd.DataFrame:
    """Bilan V/N/D à domicile et à l'extérieur, au format long."""
    rows = [
        {
            "venue": venue_label,
            "result": label,
            "color": color,
            "count": int(profile[f"{venue}_{key}"]),
        }
        for venue, venue_label in (("home", "Domicile"), ("away", "Extérieur"))
        for key, label, color in RESULTS
    ]
    return pd.DataFrame(rows)


def home_away_figure(records: pd.DataFrame) -> Any:
    """Barres horizontales empilées V/N/D, une par lieu."""
    fig = go.Figure()
    for _, label, color in RESULTS:
        part = records[records["result"] == label]
        fig.add_trace(
            go.Bar(
                y=part["venue"],
                x=part["count"],
                name=label,
                orientation="h",
                marker={"color": color, "line": {"width": 2, "color": "rgba(0,0,0,0)"}},
                text=part["count"].where(part["count"] > 0, ""),
                textposition="inside",
                insidetextanchor="middle",
                hovertemplate=f"%{{y}} · {label} : %{{x}}<extra></extra>",
            )
        )
    fig.update_layout(
        barmode="stack",
        bargap=0.45,
        height=200,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        legend={"orientation": "h", "y": -0.25, "x": 0},
        xaxis={"title": "Matchs", "gridcolor": GRID, "dtick": 1},
        yaxis={"autorange": "reversed"},
    )
    return fig


def attack_defense_figure(profiles: pd.DataFrame, selected_team_id: int | None) -> Any:
    """Nuage attaque / défense : buts marqués et encaissés par match."""
    played = profiles[profiles["played"] > 0]
    is_selected = played["team_id"] == selected_team_id
    has_selection = bool(is_selected.any())
    fig = go.Figure()
    for highlighted, part in ((False, played[~is_selected]), (True, played[is_selected])):
        if part.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=part["goals_for_per_match"],
                y=part["goals_against_per_match"],
                mode="markers+text",
                text=part["short_name"] if highlighted or not has_selection else None,
                textposition="top center",
                textfont={
                    "size": 12 if highlighted else 9,
                    "color": ACCENT if highlighted else CONTEXT,
                },
                marker={
                    "size": 14 if highlighted else 9,
                    "color": ACCENT if highlighted else CONTEXT,
                    "opacity": 1.0 if highlighted else (0.35 if has_selection else 0.7),
                    "line": {"width": 2, "color": SURFACE},
                },
                customdata=part["short_name"],
                hovertemplate=(
                    "<b>%{customdata}</b><br>Marqués : %{x:.2f} / match"
                    "<br>Encaissés : %{y:.2f} / match<extra></extra>"
                ),
                showlegend=False,
            )
        )
    fig.update_layout(
        height=300,
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        xaxis={"title": "Buts marqués / match →", "gridcolor": GRID, "zeroline": False},
        # Axe inversé : les meilleures défenses en haut.
        yaxis={
            "title": "← Buts encaissés / match",
            "gridcolor": GRID,
            "zeroline": False,
            "autorange": "reversed",
        },
    )
    return fig


def _render_league(marts: Marts) -> None:
    overview = marts.overview
    cols = st.columns(4)
    cols[0].metric("Buts par match", f"{overview['goals_per_match']:.2f}")
    cols[1].metric("Victoires à domicile", f"{overview['home_win_pct']:.0f} %")
    cols[2].metric("Nuls", f"{overview['draw_pct']:.0f} %")
    cols[3].metric("Victoires à l'extérieur", f"{overview['away_win_pct']:.0f} %")
    st.caption(
        f"Sur {int(overview['matches_played'])} matchs joués · attaque et défense de chaque club :"
    )
    st.plotly_chart(attack_defense_figure(marts.profiles, None), config={"displayModeBar": False})


def _render_team(marts: Marts, team_id: int) -> None:
    profile = marts.profiles[marts.profiles["team_id"] == team_id].iloc[0]
    league_avg = league_goals_per_team_match(marts.overview)
    played = int(profile["played"])
    if played == 0:
        st.info("Aucun match joué pour l'instant.")
        return

    def delta(value: float) -> str | None:
        return None if league_avg is None else f"{value - league_avg:+.2f} vs moy."

    scored = float(profile["goals_for_per_match"])
    conceded = float(profile["goals_against_per_match"])
    cols = st.columns(4)
    cols[0].metric("Buts marqués / match", f"{scored:.2f}", delta(scored))
    cols[1].metric(
        "Buts encaissés / match", f"{conceded:.2f}", delta(conceded), delta_color="inverse"
    )
    cols[2].metric("Clean sheets", int(profile["clean_sheets"]))
    cols[3].metric(
        "Série en cours",
        streak_text(profile["current_streak_result"], int(profile["current_streak_length"])),
    )
    st.caption(
        f"Invaincu depuis {int(profile['unbeaten_run'])} match(s) · "
        f"sans victoire depuis {int(profile['winless_run'])} match(s)"
    )
    left, right = st.columns(2)
    with left:
        st.markdown("**Domicile / extérieur**")
        st.plotly_chart(
            home_away_figure(home_away_records(profile)), config={"displayModeBar": False}
        )
    with right:
        st.markdown("**Attaque / défense dans la ligue**")
        st.plotly_chart(
            attack_defense_figure(marts.profiles, team_id), config={"displayModeBar": False}
        )


def render(marts: Marts, selected_team_id: int | None) -> None:
    """Affiche le bloc Profil."""
    if selected_team_id is None:
        st.subheader("Profil de la Ligue 1")
        _render_league(marts)
    else:
        name = marts.teams.loc[marts.teams["team_id"] == selected_team_id, "short_name"].iloc[0]
        st.subheader(f"Profil — {name}")
        _render_team(marts, selected_team_id)
