from pathlib import Path

import pytest
from pydantic import ValidationError

import ligue1
from ligue1.config import Settings, get_settings


def test_package_version() -> None:
    assert ligue1.__version__ == "0.1.0"


def test_settings_read_token_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "dummy-token")
    settings = get_settings()
    assert settings.football_data_token.get_secret_value() == "dummy-token"
    assert settings.competition_code == "FL1"
    assert settings.data_dir == Path("data")


def test_token_is_never_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "dummy-token")
    assert "dummy-token" not in repr(get_settings())


def test_missing_token_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FOOTBALL_DATA_TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)  # aucun .env lisible
    with pytest.raises(ValidationError):
        Settings()
