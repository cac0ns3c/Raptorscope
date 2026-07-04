# SPDX-License-Identifier: GPL-3.0-or-later
import json
import pathlib

from raptorscope.normalize.cron import normalize_cron

ROWS = json.loads(pathlib.Path("fixtures/velociraptor/cron_items.raw.json").read_text())
HOST = {"name": "mac-victim", "os": {"type": "macos"}}


def test_maps_each_row_to_one_ecs_doc():
    docs = normalize_cron(ROWS, HOST)
    assert len(docs) == len(ROWS)


def test_persistence_type_and_command():
    docs = normalize_cron(ROWS, HOST)
    for d in docs:
        assert d["event"]["dataset"] == "macos.persistence"
        assert d["raptorscope"]["persistence"]["type"] == "cron"
        assert d["process"]["command_line"]
        assert d["raptorscope"]["persistence"]["schedule"]


def test_malicious_curl_command_present():
    docs = normalize_cron(ROWS, HOST)
    assert any("curl" in d["process"]["command_line"] for d in docs)
