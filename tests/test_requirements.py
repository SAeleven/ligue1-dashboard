"""Les versions de l'app hébergée doivent rester celles testées localement et en CI."""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_app_requirements_match_lockfile() -> None:
    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    locked = {package["name"]: package["version"] for package in lock["package"]}

    pinned: dict[str, str] = {}
    for line in (ROOT / "app" / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if line:
            name, _, version = line.partition("==")
            assert version, f"version non épinglée : {line}"
            pinned[name] = version

    assert {"streamlit", "plotly", "pandas", "duckdb"} <= pinned.keys()
    for name, version in pinned.items():
        assert locked.get(name) == version, f"{name} : {version} ≠ uv.lock {locked.get(name)}"
