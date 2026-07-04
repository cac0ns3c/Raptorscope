# SPDX-License-Identifier: GPL-3.0-or-later
"""Command-line entry point: ingest a collection -> normalize -> index."""
import argparse

from .collection import load_collection
from .normalize.launch_items import normalize_launch_items

# artifact name (collection json stem) -> normalizer
_NORMALIZERS = {"launch_items": normalize_launch_items}


def ingest(path: str, es_url: str | None) -> int:
    """Normalize known artifacts in a collection; index if ``es_url`` given.

    Returns the total number of ECS docs produced.
    """
    artifacts, host = load_collection(path)
    docs = []
    for name, fn in _NORMALIZERS.items():
        if name in artifacts:
            docs.extend(fn(artifacts[name], host))
    if es_url:
        from elasticsearch import Elasticsearch

        from .es.indexer import bulk_index

        bulk_index(Elasticsearch(es_url), "raptorscope-persistence", docs)
    print(f"{len(docs)} docs")
    return len(docs)


def main(argv=None):
    p = argparse.ArgumentParser(prog="raptorscope")
    sub = p.add_subparsers(dest="cmd", required=True)
    ing = sub.add_parser("ingest", help="ingest a Velociraptor collection")
    ing.add_argument("path", help="collection directory or zip")
    ing.add_argument("--es", default=None, help="Elasticsearch URL (omit for dry run)")
    a = p.parse_args(argv)
    if a.cmd == "ingest":
        ingest(a.path, a.es)


if __name__ == "__main__":
    main()
