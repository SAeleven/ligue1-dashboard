import gzip
from pathlib import Path

from ligue1.archive import pack, unpack


def make_raw(root: Path, day: str, content: str = '{"matches": []}') -> Path:
    path = root / "matches" / "season=2026" / f"date={day}" / "matches.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_pack_then_unpack_roundtrip(tmp_path: Path) -> None:
    raw, archive, restored = tmp_path / "raw", tmp_path / "archive", tmp_path / "restored"
    source = make_raw(raw, "2026-11-06", '{"matches": [1, 2]}')

    packed = pack(raw, archive)
    assert packed == [archive / "matches/season=2026/date=2026-11-06/matches.json.gz"]
    assert gzip.decompress(packed[0].read_bytes()) == source.read_bytes()

    unpack(archive, restored)
    assert (restored / source.relative_to(raw)).read_bytes() == source.read_bytes()


def test_pack_is_deterministic_and_idempotent(tmp_path: Path) -> None:
    raw, archive = tmp_path / "raw", tmp_path / "archive"
    make_raw(raw, "2026-11-06")
    first = pack(raw, archive)
    content = first[0].read_bytes()

    assert pack(raw, archive) == []  # rien de changé : rien de réécrit
    assert first[0].read_bytes() == content


def test_pack_only_reports_new_or_modified_snapshots(tmp_path: Path) -> None:
    raw, archive = tmp_path / "raw", tmp_path / "archive"
    make_raw(raw, "2026-11-05")
    pack(raw, archive)
    make_raw(raw, "2026-11-06")
    changed = pack(raw, archive)
    assert [p.parent.name for p in changed] == ["date=2026-11-06"]


def test_unpack_missing_archive_is_noop(tmp_path: Path) -> None:
    assert unpack(tmp_path / "absente", tmp_path / "raw") == []
