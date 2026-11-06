"""F1 — Classement : où en est la saison ? Un clic sur une ligne sélectionne l'équipe."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app import state
from app.data import Marts
from app.format import form_icons

ZONE_MARKERS = {
    "Ligue des champions": "🟦",
    "Ligue Europa": "🟧",
    "Ligue Conférence": "🟩",
    "Barrage": "🟨",
    "Relégation": "🟥",
}
ZONE_LEGEND = " · ".join(f"{marker} {zone}" for zone, marker in ZONE_MARKERS.items())
ROW_HEIGHT = 35
RESET_COUNTER = "standings_reset"


def standings_table(standings: pd.DataFrame) -> pd.DataFrame:
    """Classement prêt à afficher, trié par rang."""
    df = standings.sort_values("position")
    return pd.DataFrame(
        {
            "tla": df["tla"],
            "Zone": df["zone"].map(ZONE_MARKERS).fillna(""),
            "Pos": df["position"],
            "Logo": df["crest_url"],
            "Équipe": df["short_name"],
            "J": df["played"],
            "G": df["won"],
            "N": df["drawn"],
            "P": df["lost"],
            "BP": df["goals_for"],
            "BC": df["goals_against"],
            "Diff": df["goal_difference"],
            "Pts": df["points"],
            "Forme": df["form"].map(form_icons),
        }
    ).reset_index(drop=True)


def reset_selection() -> None:
    """Revient à la vue Ligue 1 et décoche la ligne du tableau."""
    state.select(None)
    st.session_state[RESET_COUNTER] = st.session_state.get(RESET_COUNTER, 0) + 1


def render(marts: Marts, selected_team_id: int | None) -> None:
    """Affiche le classement ; la sélection d'une ligne met à jour l'URL."""
    table = standings_table(marts.standings)
    last_matchday = int(marts.standings["last_matchday"].max())
    key = f"standings_table_{st.session_state.get(RESET_COUNTER, 0)}"

    def on_select() -> None:
        rows = st.session_state[key].selection.rows
        state.select(str(table.iloc[rows[0]]["tla"]) if rows else None)

    st.subheader("Classement")
    st.caption(f"Après la journée {last_matchday} · clique sur une équipe pour filtrer la page")

    number = st.column_config.NumberColumn
    st.dataframe(
        table,
        key=key,
        on_select=on_select,
        selection_mode="single-row",
        hide_index=True,
        height=(len(table) + 1) * ROW_HEIGHT + 3,
        column_order=[
            "Zone",
            "Pos",
            "Logo",
            "Équipe",
            "J",
            "G",
            "N",
            "P",
            "BP",
            "BC",
            "Diff",
            "Pts",
            "Forme",
        ],
        column_config={
            "Zone": st.column_config.TextColumn("", width=28, help=ZONE_LEGEND),
            "Pos": number("#", width=32),
            "Logo": st.column_config.ImageColumn("", width=32),
            "Équipe": st.column_config.TextColumn(width="medium"),
            "J": number(help="Matchs joués", width=36),
            "G": number(help="Victoires", width=36),
            "N": number(help="Nuls", width=36),
            "P": number(help="Défaites", width=36),
            "BP": number(help="Buts marqués", width=40),
            "BC": number(help="Buts encaissés", width=40),
            "Diff": number(help="Différence de buts", format="%+d", width=44),
            "Pts": number(help="Points", width=44),
            "Forme": st.column_config.TextColumn(
                help="5 derniers matchs, le plus récent à droite", width="small"
            ),
        },
    )
    st.caption(ZONE_LEGEND)
    if selected_team_id is not None:
        st.button("↺ Voir toute la Ligue 1", on_click=reset_selection)
