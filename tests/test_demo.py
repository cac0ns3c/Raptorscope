# SPDX-License-Identifier: GPL-3.0-or-later
"""The bundled sample case ingests and drives the demo app with no setup."""
from fastapi.testclient import TestClient

from raptorscope.cli import DEMO_SAMPLE, build_demo_app, normalize_collection
from raptorscope.detect.pairing import ALL_DATASETS


def test_sample_collection_ingests():
    assert DEMO_SAMPLE.is_dir()
    docs = normalize_collection(str(DEMO_SAMPLE))
    assert len(docs) == 27
    assert {d["event"]["dataset"] for d in docs} == ALL_DATASETS


def test_demo_app_serves_sample_case_with_alerts():
    client = TestClient(build_demo_app())
    cases = client.get("/cases").json()
    assert [c["name"] for c in cases] == ["mac-victim"]
    alerts = client.get("/cases/mac-victim/alerts").json()
    assert alerts
    assert {a["dataset"] for a in alerts} == ALL_DATASETS
