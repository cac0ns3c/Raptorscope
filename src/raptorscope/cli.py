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


def build_serve_app(es_url: str | None = None, collection: str | None = None):
    """Build the FastAPI app for ``serve``.

    ``collection`` (a dir/zip) runs fully offline over an in-memory store —
    handy for demos; ``es_url`` serves a live Elasticsearch via ``ESStore``.
    """
    from .api.app import create_app
    from .api.store import InMemoryStore

    if collection is not None:
        store = InMemoryStore(normalize_collection(collection))
    elif es_url is not None:
        from elasticsearch import Elasticsearch

        from .es.store import ESStore

        store = ESStore(Elasticsearch(es_url))
    else:
        raise ValueError("serve requires either --collection or --es")
    return create_app(store)


def serve(es_url, collection, host, port):  # pragma: no cover - runs a server
    import uvicorn

    uvicorn.run(build_serve_app(es_url=es_url, collection=collection), host=host, port=port)


def main(argv=None):
    p = argparse.ArgumentParser(prog="raptorscope")
    sub = p.add_subparsers(dest="cmd", required=True)
    ing = sub.add_parser("ingest", help="ingest a Velociraptor collection")
    ing.add_argument("path", help="collection directory or zip")
    ing.add_argument("--es", default=None, help="Elasticsearch URL (omit for dry run)")

    srv = sub.add_parser("serve", help="run the query API")
    srv.add_argument("--es", default=None, help="Elasticsearch URL")
    srv.add_argument(
        "--collection", default=None, help="serve a collection dir/zip offline"
    )
    srv.add_argument("--host", default="127.0.0.1")
    srv.add_argument("--port", type=int, default=8000)

    a = p.parse_args(argv)
    if a.cmd == "ingest":
        ingest(a.path, a.es)
    elif a.cmd == "serve":
        serve(a.es, a.collection, a.host, a.port)


if __name__ == "__main__":
    main()
