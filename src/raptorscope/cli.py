# SPDX-License-Identifier: GPL-3.0-or-later
"""Command-line entry point: ingest a collection -> normalize -> index."""
import argparse

from .collection import enrich_host, load_collection
from .normalize.btm import normalize_btm
from .normalize.config_profiles import normalize_config_profiles
from .normalize.cron import normalize_cron
from .normalize.inventory import normalize_inventory
from .normalize.launch_items import normalize_launch_items
from .normalize.login_items import normalize_login_items
from .normalize.processes import normalize_processes
from .normalize.quarantine import normalize_quarantine
from .normalize.tcc import normalize_tcc

# collection json stem -> normalizer for that artifact
_NORMALIZERS = {
    "launch_items": normalize_launch_items,
    "login_items": normalize_login_items,
    "cron_items": normalize_cron,
    "config_profiles": normalize_config_profiles,
    "btm_items": normalize_btm,
    "processes": normalize_processes,
    "quarantine": normalize_quarantine,
    "tcc": normalize_tcc,
    "installed_apps": normalize_inventory,
}


def _index_for(dataset: str) -> str:
    """Map an ECS dataset to its raptorscope index name (``raptorscope-*``)."""
    return "raptorscope-" + dataset.replace(".", "-")


def normalize_collection(path: str) -> list[dict]:
    """Load a collection and normalize every known artifact to ECS docs."""
    artifacts, raw_host = load_collection(path)
    host = enrich_host(raw_host)
    docs: list[dict] = []
    for name, fn in _NORMALIZERS.items():
        if name in artifacts:
            docs.extend(fn(artifacts[name], host))
    return docs


def ingest(path: str, es_url: str | None) -> int:
    """Normalize known artifacts in a collection; index if ``es_url`` given.

    Returns the total number of ECS docs produced.
    """
    docs = normalize_collection(path)
    if es_url:
        from elasticsearch import Elasticsearch

        from .es.indexer import bulk_index

        client = Elasticsearch(es_url)
        # Route each doc to a per-dataset index under the raptorscope-* pattern.
        by_index: dict[str, list[dict]] = {}
        for d in docs:
            by_index.setdefault(_index_for(d["event"]["dataset"]), []).append(d)
        for index, group in by_index.items():
            bulk_index(client, index, group)
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
