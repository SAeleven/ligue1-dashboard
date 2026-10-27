"""Construit une couche raw de test à partir des fixtures.

Utilisé par les tests et par la CI (`dbt build` sur données fictives) :
    python -m tests.seed ci_data
"""

import shutil
import sys
from datetime import date
from pathlib import Path

from ligue1.client import Endpoint
from ligue1.extract import raw_path

FIXTURES = Path(__file__).parent / "fixtures"
ENDPOINTS: tuple[Endpoint, ...] = ("matches", "standings", "teams", "scorers")
SEED_DAY = date(2026, 8, 16)


def seed_raw(data_dir: Path, day: date = SEED_DAY, season: int = 2026) -> list[Path]:
    """Copie chaque fixture à son emplacement de la couche raw."""
    written = []
    for endpoint in ENDPOINTS:
        target = raw_path(data_dir, endpoint, season, day)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(FIXTURES / f"{endpoint}.json", target)
        written.append(target)
    return written


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "ci_data")
    for path in seed_raw(out):
        print(path)
