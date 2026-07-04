# SPDX-License-Identifier: GPL-3.0-or-later


def test_docs_index_lists_meaningful_docs(client):
    r = client.get("/docs")
    assert r.status_code == 200
    ids = {d["id"] for d in r.json()}
    assert {"readme", "install", "demo", "kibana"} <= ids
    # internal design/plan docs are NOT exposed
    assert "spec" not in ids and "plan" not in ids


def test_get_doc_returns_markdown(client):
    r = client.get("/docs/readme")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == "readme"
    assert "Raptorscope" in body["markdown"]


def test_unknown_doc_404(client):
    assert client.get("/docs/nope").status_code == 404


def test_docs_open_without_auth():
    # docs remain readable even when the API requires auth for case data
    from fastapi.testclient import TestClient

    from raptorscope.api.app import create_app
    from raptorscope.api.auth import AuthConfig
    from raptorscope.api.store import InMemoryStore
    from tests.api.conftest import seed_docs

    c = TestClient(
        create_app(InMemoryStore(seed_docs()), auth=AuthConfig(username="a", password="b"))
    )
    assert c.get("/cases").status_code == 401
    assert c.get("/docs").status_code == 200
