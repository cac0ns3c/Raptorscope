# SPDX-License-Identifier: GPL-3.0-or-later
"""The `serve` CLI helper can build an app from an offline collection dir."""
import json
import pathlib
import shutil

from fastapi.testclient import TestClient

from raptorscope.cli import build_serve_app

FIX = pathlib.Path("fixtures/velociraptor")


def _collection(dst: pathlib.Path):
    dst.mkdir(parents=True, exist_ok=True)
    for stem, fname in {
        "launch_items": "launch_items.raw.json",
        "tcc": "tcc.raw.json",
    }.items():
        shutil.copyfile(FIX / fname, dst / f"{stem}.json")
    (dst / "host.json").write_text(
        json.dumps({"name": "mac-demo", "os": {"type": "macos"}})
    )


def test_build_serve_app_from_collection(tmp_path):
    col = tmp_path / "col"
    _collection(col)
    app = build_serve_app(es_url=None, collection=str(col))
    client = TestClient(app)
    cases = client.get("/cases").json()
    assert [c["name"] for c in cases] == ["mac-demo"]
    alerts = client.get("/cases/mac-demo/alerts").json()
    assert any(a["dataset"] == "macos.tcc" for a in alerts)
