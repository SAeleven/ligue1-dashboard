"""Dashboard Ligue 1 — page unique.

Lancement : `uv run streamlit run app/main.py` (ou `make app`).
Le classement (F1) occupe la colonne de gauche ; Évolution (F2), Profil (F3) et
Matchs (F4) sont empilés à droite. Sélectionner une équipe filtre tous les blocs.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:  # `streamlit run` n'ajoute que le dossier app/
    sys.path.insert(0, str(ROOT))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from app import data, state  # noqa: E402
from app.blocks import evolution, matches, profile, scorers, standings  # noqa: E402
from app.format import season_label  # noqa: E402

st.set_page_config(page_title="Ligue 1 Dashboard", page_icon="⚽", layout="wide")

try:
    marts = data.load_from_env()
except data.DataUnavailableError as exc:
    st.title("Ligue 1 Dashboard")
    st.error(
        "Les données ne sont pas encore disponibles. Lance le pipeline : "
        "`make extract`, `make load` puis `make transform`."
    )
    st.caption(f"Détail : {exc}")
    st.stop()

selected = state.selected_team_id(marts.teams)
as_of = marts.overview["data_as_of"]

st.title(f"Ligue 1 · saison {season_label(marts.season)}")
st.caption(
    f"Données au {as_of:%d/%m/%Y} · mises à jour chaque jour · source football-data.org"
    if pd.notna(as_of)
    else "Source football-data.org"
)

if selected is not None:
    team = marts.teams[marts.teams["team_id"] == selected].iloc[0]
    st.info(
        f"Vue filtrée sur **{team['team_name']}** · « ↺ Voir toute la Ligue 1 » "
        "sous le classement pour revenir à la vue d'ensemble."
    )

left, right = st.columns([5, 7], gap="large")
with left:
    standings.render(marts, selected)
    scorers.render(marts, selected)
with right:
    with st.container(border=True):
        evolution.render(marts, selected)
    with st.container(border=True):
        profile.render(marts, selected)
    with st.container(border=True):
        matches.render(marts, selected)
