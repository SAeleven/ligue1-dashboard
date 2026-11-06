"""Archivage de la couche raw sur la branche Git `data`.

Les runners GitHub sont éphémères : l'historique des snapshots vit sur la branche
orpheline `data`, compressé en gzip (environ 10 fois plus léger). Le pipeline
décompresse l'archive avant le chargement, puis y ajoute le snapshot du jour.

Usage :
    python -m ligue1.archive unpack <archive> <data/raw>
    python -m ligue1.archive pack <data/raw> <archive>

La compression est déterministe (pas d'horodatage dans l'en-tête gzip) : un
fichier inchangé produit exactement les mêmes octets, donc aucun diff Git.
"""

from __future__ import annotations

import argparse
import gzip
import logging
from collections.abc import Sequence
from pathlib import Path

logger = logging.getLogger(__name__)


def _write_if_changed(target: Path, content: bytes) -> bool:
    """Écrit `content` dans `target` sauf si le fichier est déjà identique."""
    if target.exists() and target.read_bytes() == content:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return True


def pack(raw_dir: Path, archive_dir: Path) -> list[Path]:
    """Compresse chaque `*.json` de `raw_dir` ; renvoie les archives créées ou modifiées."""
    changed: list[Path] = []
    for source in sorted(raw_dir.rglob("*.json")):
        relative = source.relative_to(raw_dir)
        target = archive_dir / relative.with_name(relative.name + ".gz")
        if _write_if_changed(target, gzip.compress(source.read_bytes(), mtime=0)):
            changed.append(target)
    return changed


def unpack(archive_dir: Path, raw_dir: Path) -> list[Path]:
    """Décompresse chaque `*.json.gz` de `archive_dir` vers `raw_dir`."""
    written: list[Path] = []
    if not archive_dir.exists():
        return written
    for source in sorted(archive_dir.rglob("*.json.gz")):
        relative = source.relative_to(archive_dir)
        target = raw_dir / relative.with_name(relative.name.removesuffix(".gz"))
        _write_if_changed(target, gzip.decompress(source.read_bytes()))
        written.append(target)
    return written


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée CLI."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Archive gzip de la couche raw.")
    parser.add_argument("action", choices=["pack", "unpack"])
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)

    if args.action == "pack":
        changed = pack(args.source, args.destination)
        logger.info("%d archive(s) créée(s) ou modifiée(s) dans %s", len(changed), args.destination)
    else:
        written = unpack(args.source, args.destination)
        logger.info("%d fichier(s) restauré(s) dans %s", len(written), args.destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
