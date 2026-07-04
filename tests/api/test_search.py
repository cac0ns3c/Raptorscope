# SPDX-License-Identifier: GPL-3.0-or-later


def test_free_text_search_matches_leaf_values(client):
    r = client.get("/cases/mac-victim/search", params={"q": "/private/tmp"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert all("_id" in d for d in body["items"])
    # every hit really contains the term somewhere
    import json

    for d in body["items"]:
        assert "/private/tmp" in json.dumps(d).lower()


def test_search_scoped_by_dataset(client):
    body = client.get(
        "/cases/mac-victim/search",
        params={"q": "com", "dataset": "macos.tcc"},
    ).json()
    assert body["total"] >= 1
    assert all(d["event"]["dataset"] == "macos.tcc" for d in body["items"])


def test_structured_field_filter(client):
    body = client.get(
        "/cases/mac-victim/search",
        params={"field": "raptorscope.persistence.type", "value": "btm", "op": "eq"},
    ).json()
    assert body["total"] >= 1
    assert all(
        d["raptorscope"]["persistence"]["type"] == "btm" for d in body["items"]
    )


def test_empty_query_returns_case_docs(client):
    body = client.get("/cases/mac-victim/search").json()
    assert body["total"] == 22


def test_search_unknown_case_404(client):
    assert client.get("/cases/nope/search", params={"q": "x"}).status_code == 404
