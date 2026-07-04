# SPDX-License-Identifier: GPL-3.0-or-later
from tests.api.conftest import DIRTY_DOC_COUNT


def test_timeline_sorted_desc_and_mixed(client):
    r = client.get("/cases/mac-victim/timeline?limit=1000")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == DIRTY_DOC_COUNT
    stamps = [row["timestamp"] for row in rows]
    assert stamps == sorted(stamps, reverse=True)
    assert len({row["dataset"] for row in rows}) >= 4
    for row in rows:
        assert row["doc_id"]
        assert row["summary"]
        assert row["dataset"]
        assert "time_source" in row  # provenance surfaced (mtime vs event)


def test_timeline_respects_limit(client):
    rows = client.get("/cases/mac-victim/timeline?limit=5").json()
    assert len(rows) == 5


def test_timeline_doc_id_resolves_via_artifact_view(client):
    rows = client.get("/cases/mac-victim/timeline?limit=1000").json()
    row = next(r for r in rows if r["dataset"] == "macos.tcc")
    items = client.get(
        f"/cases/mac-victim/artifacts/{row['dataset']}?limit=1000"
    ).json()["items"]
    assert row["doc_id"] in {d["_id"] for d in items}


def test_timeline_unknown_case_404(client):
    assert client.get("/cases/nope/timeline").status_code == 404
