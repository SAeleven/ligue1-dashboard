"""Configuration lue depuis l'environnement (`.env` en local, secrets GitHub en CI)."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres du pipeline. Aucun chemin ni token en dur (spec §7)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    football_data_token: SecretStr = Field(
        description="Token de l'API football-data.org (en-tête X-Auth-Token)."
    )
    football_data_base_url: str = "https://api.football-data.org/v4"
    competition_code: str = "FL1"
    data_dir: Path = Path("data")
    duckdb_path: Path = Path("data/ligue1.duckdb")


def get_settings() -> Settings:
    """Construit les paramètres ; échoue si le token est absent."""
    return Settings()
