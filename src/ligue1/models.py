"""Modèles Pydantic des réponses de l'API football-data.org v4.

Ils servent de garde-fou : si l'API change le format d'un champ utilisé par le
pipeline, la validation échoue et le run s'arrête au lieu d'écrire des données
corrompues. Les champs non utilisés sont ignorés (`extra="ignore"`), donc l'ajout
d'un champ par l'API ne casse rien.

La couche raw stocke le JSON tel que reçu ; ces modèles ne servent qu'à valider.
"""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from ligue1.client import Endpoint


class ApiModel(BaseModel):
    """Base commune : alias camelCase de l'API, champs inconnus ignorés."""

    model_config = ConfigDict(alias_generator=to_camel, extra="ignore", frozen=True)


class Competition(ApiModel):
    """Compétition (ex. Ligue 1, code FL1)."""

    id: int
    name: str
    code: str


class Season(ApiModel):
    """Saison d'une compétition."""

    id: int
    start_date: date
    end_date: date
    current_matchday: int | None = None


class TeamRef(ApiModel):
    """Équipe telle qu'elle apparaît dans un match ou un classement."""

    id: int
    name: str
    short_name: str | None = None
    tla: str | None = None
    crest: str | None = None


class Goals(ApiModel):
    """Score d'une période ; `None` tant que le match n'est pas joué."""

    home: int | None
    away: int | None


class Score(ApiModel):
    """Score final et mi-temps."""

    winner: Literal["HOME_TEAM", "AWAY_TEAM", "DRAW"] | None
    duration: str
    full_time: Goals
    half_time: Goals


class Match(ApiModel):
    """Match de la saison, joué ou à venir."""

    id: int
    utc_date: datetime
    status: str
    matchday: int | None
    stage: str
    home_team: TeamRef
    away_team: TeamRef
    score: Score
    last_updated: datetime


class MatchesResponse(ApiModel):
    """Réponse de `/competitions/FL1/matches`."""

    competition: Competition
    matches: list[Match]


class TableRow(ApiModel):
    """Ligne de classement."""

    position: int
    team: TeamRef
    played_games: int
    form: str | None = None
    won: int
    draw: int
    lost: int
    points: int
    goals_for: int
    goals_against: int
    goal_difference: int


class Standing(ApiModel):
    """Un classement : général, domicile ou extérieur."""

    stage: str
    type: Literal["TOTAL", "HOME", "AWAY"]
    table: list[TableRow]


class StandingsResponse(ApiModel):
    """Réponse de `/competitions/FL1/standings`."""

    competition: Competition
    season: Season
    standings: list[Standing]


class Team(ApiModel):
    """Équipe engagée dans la compétition."""

    id: int
    name: str
    short_name: str | None = None
    tla: str | None = None
    crest: str | None = None
    founded: int | None = None
    venue: str | None = None


class TeamsResponse(ApiModel):
    """Réponse de `/competitions/FL1/teams`."""

    competition: Competition
    season: Season
    teams: list[Team]


class Player(ApiModel):
    """Joueur (version réduite)."""

    id: int
    name: str


class Scorer(ApiModel):
    """Ligne du classement des buteurs."""

    player: Player
    team: TeamRef
    played_matches: int | None = None
    goals: int
    assists: int | None = None
    penalties: int | None = None


class ScorersResponse(ApiModel):
    """Réponse de `/competitions/FL1/scorers`."""

    competition: Competition
    season: Season
    scorers: list[Scorer]


RESPONSE_MODELS: dict[Endpoint, type[ApiModel]] = {
    "matches": MatchesResponse,
    "standings": StandingsResponse,
    "teams": TeamsResponse,
    "scorers": ScorersResponse,
}


def validate_payload(endpoint: Endpoint, payload: dict[str, Any]) -> ApiModel:
    """Valide une réponse brute ; lève `pydantic.ValidationError` si elle est mal formée."""
    return RESPONSE_MODELS[endpoint].model_validate(payload)
