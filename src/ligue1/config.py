"""Configuration lue depuis l'environnement (`.env` en local, secrets GitHub en CI)."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class MissingTokenError(RuntimeError):
    """Le token API est requis mais absent."""


class Settings(BaseSettings):
    """Paramètres du pipeline. Aucun chemin ni token en dur (spec §7).

    Le token n'est exigé que par l'extraction : le chargement et dbt tournent
    sans lui (CI sur fixtures, développement hors ligne).
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    football_data_token: SecretStr | None = Field(
        default=None,
        description="Token de l'API football-data.org (en-tête X-Auth-Token).",
    )
    football_data_base_url: str = "https://api.football-data.org/v4"
    competition_code: str = "FL1"
    data_dir: Path = Path("data")
    duckdb_path: Path = Path("data/ligue1.duckdb")

    def require_token(self) -> str:
        """Renvoie le token en clair, ou lève une erreur explicite s'il manque."""
        if self.football_data_token is None or not self.football_data_token.get_secret_value():
            raise MissingTokenError(
                "FOOTBALL_DATA_TOKEN manquant : renseigne-le dans .env (voir .env.example)."
            )
        return self.football_data_token.get_secret_value()


def get_settings() -> Settings:
    """Construit les paramètres depuis l'environnement et `.env`."""
    return Settings()
