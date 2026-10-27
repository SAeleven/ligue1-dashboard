from pathlib import Path

import pytest

import ligue1
from ligue1.config import MissingTokenError, Settings, get_settings


def test_package_version() -> None:
    assert ligue1.__version__ == "0.1.0"


def test_settings_read_token_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "dummy-token")
    settings = get_settings()
    assert settings.require_token() == "dummy-token"
    assert settings.competition_code == "FL1"
    assert settings.data_dir == Path("data")


def test_token_is_never_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FOOTBALL_DATA_TOKEN", "dummy-token")
    assert "dummy-token" not in repr(get_settings())


@pytest.mark.parametrize("value", [None, ""])
def test_missing_token_fails_only_when_required(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, value: str | None
) -> None:
    monkeypatch.delenv("FOOTBALL_DATA_TOKEN", raising=False)
    if value is not None:
        monkeypatch.setenv("FOOTBALL_DATA_TOKEN", value)
    monkeypatch.chdir(tmp_path)  # aucun .env lisible
    settings = Settings()  # le chargement et dbt n'ont pas besoin du token
    with pytest.raises(MissingTokenError):
        settings.require_token()
