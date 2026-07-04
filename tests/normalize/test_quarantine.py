# SPDX-License-Identifier: GPL-3.0-or-later
import json
import pathlib

from raptorscope.normalize.quarantine import normalize_quarantine

ROWS = json.loads(pathlib.Path("fixtures/velociraptor/quarantine.raw.json").read_text())
HOST = {"name": "mac-victim", "os": {"type": "macos"}}


def test_maps_each_row_to_one_ecs_doc():
    docs = normalize_quarantine(ROWS, HOST)
    assert len(docs) == len(ROWS)


def test_quarantine_dataset_and_fields():
    docs = normalize_quarantine(ROWS, HOST)
    for d in docs:
        assert d["event"]["dataset"] == "macos.quarantine"
        assert d["event"]["category"] == ["file"]
        assert d["file"]["path"]
        assert d["url"]["full"]
    firefox = next(d for d in docs if d["file"]["name"] == "Firefox.dmg")
    assert firefox["process"]["name"] == "Safari"
    assert firefox["url"]["original"].startswith("https://www.mozilla.org")


def test_double_extension_payload_present():
    docs = normalize_quarantine(ROWS, HOST)
    assert any(d["file"]["path"].endswith(".command") for d in docs)
