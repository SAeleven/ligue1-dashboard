"""Mise en forme commune : couleurs, résultats, dates en français.

Couleurs : palette de référence de visualisation (accent bleu, gris de contexte)
et couleurs de statut réservées aux résultats, toujours accompagnées d'une lettre.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

ACCENT = "#3987e5"  # pas « sombre » de la palette de référence
SURFACE = "#0e1117"  # fond du thème sombre de Streamlit
CONTEXT = "#898781"
WIN = "#0ca30c"
DRAW = "#898781"
LOSS = "#d03b3b"

RESULT_LABELS = {"W": "V", "D": "N", "L": "D"}
RESULT_ICONS = {"W": "🟢", "D": "⚪", "L": "🔴"}
RESULT_WORDS = {
    "W": ("victoire", "victoires"),
    "D": ("nul", "nuls"),
    "L": ("défaite", "défaites"),
}

ZONE_ICONS = {
    "Ligue des champions": "🔵",
    "Ligue Europa": "🟠",
    "Ligue Conférence": "🟢",
    "Barrage": "🟡",
    "Relégation": "🔴",
}

STATUS_LABELS = {
    "POSTPONED": "Reporté",
    "SUSPENDED": "Suspendu",
    "CANCELLED": "Annulé",
    "IN_PLAY": "En cours",
    "PAUSED": "Mi-temps",
}

_WEEKDAYS = ("lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim.")


def form_icons(form: object) -> str:
    """'WDLWW' -> '🟢⚪🔴🟢🟢' (du plus ancien au plus récent)."""
    if not isinstance(form, str):
        return ""
    return "".join(RESULT_ICONS.get(letter, "") for letter in form)


def streak_text(result: object, length: int) -> str:
    """Décrit une série : '3 victoires', '1 nul'."""
    if not isinstance(result, str) or result not in RESULT_WORDS or length <= 0:
        return "—"
    singular, plural = RESULT_WORDS[result]
    return f"{length} {singular if length == 1 else plural}"


def kickoff_label(moment: datetime) -> str:
    """'sam. 08/11 · 21:00'."""
    return f"{_WEEKDAYS[moment.weekday()]} {moment:%d/%m · %H:%M}"


def season_label(season: int) -> str:
    """2026 -> '2026-27'."""
    return f"{season}-{(season + 1) % 100:02d}"


def score_label(home_goals: object, away_goals: object, status: str) -> str:
    """'2 - 1' pour un match joué, sinon le statut ou un tiret."""
    if status in STATUS_LABELS:
        return STATUS_LABELS[status]
    if pd.isna(home_goals) or pd.isna(away_goals):
        return "–"
    return f"{int(pd.to_numeric(home_goals))} - {int(pd.to_numeric(away_goals))}"
