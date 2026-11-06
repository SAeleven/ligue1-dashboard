"""Équipe sélectionnée, partagée par tous les blocs.

La source de vérité est le paramètre d'URL `?equipe=<SIGLE>` : une vue filtrée se
partage par simple lien. Un clic dans le classement met à jour ce paramètre ;
un nouveau clic sur la même ligne, ou le bouton de réinitialisation, l'efface.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

PARAM = "equipe"


def team_id_from_tla(teams: pd.DataFrame, tla: str | None) -> int | None:
    """Identifiant de l'équipe dont le sigle est `tla` (insensible à la casse)."""
    if not tla:
        return None
    match = teams.loc[teams["tla"].str.upper() == tla.upper(), "team_id"]
    return int(match.iloc[0]) if not match.empty else None


def selected_team_id(teams: pd.DataFrame) -> int | None:
    """Équipe sélectionnée d'après l'URL, ou None pour la vue Ligue 1."""
    return team_id_from_tla(teams, st.query_params.get(PARAM))


def select(tla: str | None) -> None:
    """Sélectionne une équipe par son sigle, ou revient à la vue Ligue 1."""
    if tla:
        st.query_params[PARAM] = tla
    elif PARAM in st.query_params:
        del st.query_params[PARAM]
