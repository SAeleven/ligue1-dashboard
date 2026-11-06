"""F2 — Évolution : comment la saison s'est-elle construite ?

Une ligne par équipe, en gris ; l'équipe sélectionnée est mise en avant
(principe « une en couleur, les autres en retrait » plutôt que 18 couleurs).
"""

from __future__ import annotations

from typing import Any, Literal

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.data import Marts
from app.format import ACCENT, CONTEXT

Metric = Literal["position", "points"]
METRIC_LABELS: dict[str, Metric] = {"Rang": "position", "Points": "points"}
GRID = "rgba(137, 135, 129, 0.2)"


def evolution_figure(
    history: pd.DataFrame,
    standings: pd.DataFrame,
    selected_team_id: int | None,
    metric: Metric = "position",
) -> Any:
    """Courbes rang (ou points) par journée."""
    order = standings.sort_values("position")["team_id"].tolist()
    n_teams = len(order)
    has_selection = selected_team_id is not None
    fig = go.Figure()

    def add_team(team_id: int, highlighted: bool) -> None:
        team = history[history["team_id"] == team_id].sort_values("matchday")
        if team.empty:
            return
        name = str(team["short_name"].iloc[0])
        fig.add_trace(
            go.Scatter(
                x=team["matchday"],
                y=team[metric],
                name=name,
                mode="lines+markers" if highlighted else "lines",
                line={
                    "color": ACCENT if highlighted else CONTEXT,
                    "width": 3 if highlighted else 1.5,
                },
                marker={"size": 8, "color": ACCENT},
                opacity=1.0 if highlighted else (0.25 if has_selection else 0.55),
                hovertemplate=(
                    f"<b>{name}</b><br>Journée %{{x}}<br>"
                    + ("%{y}e" if metric == "position" else "%{y} pts")
                    + "<extra></extra>"
                ),
                showlegend=False,
            )
        )
        # Étiquette directe en bout de courbe (rangs distincts : pas de chevauchement).
        if highlighted or (metric == "position" and not has_selection):
            last = team.iloc[-1]
            fig.add_annotation(
                x=last["matchday"],
                y=last[metric],
                text=str(last["tla"]),
                showarrow=False,
                xanchor="left",
                xshift=6,
                font={
                    "size": 12 if highlighted else 10,
                    "color": ACCENT if highlighted else CONTEXT,
                },
            )

    for team_id in order:
        if team_id != selected_team_id:
            add_team(team_id, highlighted=False)
    if has_selection and selected_team_id is not None:
        add_team(selected_team_id, highlighted=True)

    yaxis: dict[str, Any] = {"gridcolor": GRID, "zeroline": False}
    if metric == "position":
        yaxis |= {
            "title": "Rang",
            "range": [n_teams + 0.5, 0.5],
            "tickvals": list(range(1, n_teams + 1, 2 if n_teams > 10 else 1)),
        }
    else:
        yaxis |= {"title": "Points", "rangemode": "tozero"}

    fig.update_layout(
        height=380,
        margin={"l": 10, "r": 40, "t": 10, "b": 10},
        hovermode="closest",
        xaxis={
            "title": "Journée",
            "gridcolor": GRID,
            "dtick": 1 if history["matchday"].max() <= 12 else 2,
        },
        yaxis=yaxis,
    )
    return fig


def render(marts: Marts, selected_team_id: int | None) -> None:
    """Affiche le bloc Évolution."""
    st.subheader("Évolution")
    choice = st.segmented_control(
        "Indicateur",
        list(METRIC_LABELS),
        default="Rang",
        key="evolution_metric",
        label_visibility="collapsed",
    )
    metric = METRIC_LABELS.get(choice or "Rang", "position")
    if marts.history.empty:
        st.info("Aucune journée jouée pour l'instant.")
        return
    st.plotly_chart(
        evolution_figure(marts.history, marts.standings, selected_team_id, metric),
        config={"displayModeBar": False},
    )
    if selected_team_id is None:
        st.caption("Sélectionne une équipe dans le classement pour mettre sa courbe en avant.")
