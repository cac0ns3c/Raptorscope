# SPDX-License-Identifier: GPL-3.0-or-later
"""Command-line entry point: ingest a collection -> normalize -> index."""
import argparse
import pathlib

from .collection import enrich_host, load_collection

# The committed sample collection that `raptorscope demo` serves out of the box.
DEMO_SAMPLE = pathlib.Path(__file__).resolve().parents[2] / "samples" / "mac-victim"
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
        from .es.template import put_index_template

        client = Elasticsearch(es_url)
        put_index_template(client)
        # Route each doc to a per-dataset index under the raptorscope-* pattern.
        by_index: dict[str, list[dict]] = {}
        for d in docs:
            by_index.setdefault(_index_for(d["event"]["dataset"]), []).append(d)
        for index, group in by_index.items():
            bulk_index(client, index, group)
    print(f"{len(docs)} docs")
    return len(docs)


def build_serve_app(
    es_url: str | None = None,
    collection: str | None = None,
    auth_user: str | None = None,
    auth_pass: str | None = None,
):
    """Build the FastAPI app for ``serve``.

    ``collection`` (a dir/zip) runs fully offline over an in-memory store —
    handy for demos; ``es_url`` serves a live Elasticsearch via ``ESStore``.
    Passing ``auth_user``/``auth_pass`` (or the ``RAPTORSCOPE_AUTH_*`` env vars)
    requires clients to log in for a bearer token.
    """
    from .api.app import create_app
    from .api.auth import AuthConfig
    from .api.store import InMemoryStore

    if collection is not None:
        store = InMemoryStore(normalize_collection(collection))
    elif es_url is not None:
        from elasticsearch import Elasticsearch

        from .es.store import ESStore

        store = ESStore(Elasticsearch(es_url))
    else:
        raise ValueError("serve requires either --collection or --es")

    auth = AuthConfig.from_env()
    if auth_user is not None:
        auth.username = auth_user
    if auth_pass is not None:
        auth.password = auth_pass
    return create_app(store, auth=auth)


def build_demo_app(collection=None):
    """Build the API app over the bundled sample case (fully offline)."""
    return build_serve_app(collection=str(collection or DEMO_SAMPLE))


def serve(es_url, collection, host, port, auth_user=None, auth_pass=None):  # pragma: no cover - runs a server
    import uvicorn

    app = build_serve_app(
        es_url=es_url,
        collection=collection,
        auth_user=auth_user,
        auth_pass=auth_pass,
    )
    uvicorn.run(app, host=host, port=port)


def demo(host, port):  # pragma: no cover - runs a server
    import uvicorn

    print(f"raptorscope demo: serving sample case from {DEMO_SAMPLE}")
    uvicorn.run(build_demo_app(), host=host, port=port)


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
    srv.add_argument("--auth-user", default=None, help="require login as this user")
    srv.add_argument("--auth-pass", default=None, help="password for --auth-user")

    dem = sub.add_parser("demo", help="serve the bundled sample case (no setup)")
    dem.add_argument("--host", default="127.0.0.1")
    dem.add_argument("--port", type=int, default=8000)

    a = p.parse_args(argv)
    if a.cmd == "ingest":
        ingest(a.path, a.es)
    elif a.cmd == "serve":
        serve(a.es, a.collection, a.host, a.port, a.auth_user, a.auth_pass)
    elif a.cmd == "demo":
        demo(a.host, a.port)


if __name__ == "__main__":
    main()
