"""F5 — Buteurs : meilleurs buteurs de la ligue, ou de l'équipe sélectionnée."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from app.data import Marts


def top_scorers(scorers: pd.DataFrame, team_id: int | None = None, n: int = 10) -> pd.DataFrame:
    """Les n premiers buteurs (de la ligue, ou d'une équipe), prêts à afficher."""
    df = scorers if team_id is None else scorers[scorers["team_id"] == team_id]
    df = df.sort_values(["goals", "player_name"], ascending=[False, True]).head(n)
    return pd.DataFrame(
        {
            "Rang": df["rank"],
            "Logo": df["crest_url"],
            "Joueur": df["player_name"],
            "Équipe": df["team"],
            "Buts": df["goals"],
            "Passes déc.": df["assists"],
            "dont pen.": df["penalties"],
        }
    ).reset_index(drop=True)


def render(marts: Marts, selected_team_id: int | None) -> None:
    """Affiche le bloc Buteurs."""
    st.subheader("Buteurs")
    table = top_scorers(marts.scorers, selected_team_id)
    if table.empty:
        st.caption(
            "Aucun buteur dans le top 50 de la ligue." if selected_team_id else "Pas de données."
        )
        return
    if selected_team_id is not None:
        table = table.drop(columns=["Logo", "Équipe"])
        st.caption("Rang au classement général des buteurs.")
    st.dataframe(
        table,
        hide_index=True,
        column_config={
            "Rang": st.column_config.NumberColumn("#", width=32),
            "Logo": st.column_config.ImageColumn("", width=28),
            "Buts": st.column_config.NumberColumn(width=44),
            "Passes déc.": st.column_config.NumberColumn(help="Passes décisives", width=60),
            "dont pen.": st.column_config.NumberColumn(help="Buts sur penalty", width=56),
        },
    )
