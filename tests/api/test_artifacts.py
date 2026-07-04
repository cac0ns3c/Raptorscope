# SPDX-License-Identifier: GPL-3.0-or-later


def test_artifact_view_returns_dataset_docs(client):
    r = client.get("/cases/mac-victim/artifacts/macos.persistence")
    assert r.status_code == 200
    body = r.json()
    assert body["dataset"] == "macos.persistence"
    assert body["total"] == 12
    assert all(d["event"]["dataset"] == "macos.persistence" for d in body["items"])
    assert all("_id" in d for d in body["items"])


def test_artifact_view_default_limit(client):
    body = client.get("/cases/mac-victim/artifacts/macos.persistence").json()
    assert len(body["items"]) == 12  # under default limit of 50


def test_artifact_view_pagination(client):
    full = client.get(
        "/cases/mac-victim/artifacts/macos.persistence?limit=100"
    ).json()["items"]
    page = client.get(
        "/cases/mac-victim/artifacts/macos.persistence?limit=5&offset=5"
    ).json()
    assert page["total"] == 12
    ids_full = [d["_id"] for d in full][5:10]
    ids_page = [d["_id"] for d in page["items"]]
    assert ids_page == ids_full


def test_artifact_view_unknown_dataset_empty(client):
    body = client.get("/cases/mac-victim/artifacts/macos.nope").json()
    assert body["total"] == 0
    assert body["items"] == []


def test_artifact_view_unknown_case_404(client):
    assert (
        client.get("/cases/nope/artifacts/macos.process").status_code == 404
    )
