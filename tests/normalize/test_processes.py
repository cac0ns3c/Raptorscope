# SPDX-License-Identifier: GPL-3.0-or-later
import json
import pathlib

from raptorscope.normalize.processes import normalize_processes

ROWS = json.loads(pathlib.Path("fixtures/velociraptor/processes.raw.json").read_text())
HOST = {"name": "mac-victim", "os": {"type": "macos"}}


def test_maps_each_row_to_one_ecs_doc():
    docs = normalize_processes(ROWS, HOST)
    assert len(docs) == len(ROWS)


def test_process_dataset_and_fields():
    docs = normalize_processes(ROWS, HOST)
    for d in docs:
        assert d["event"]["dataset"] == "macos.process"
        assert d["event"]["category"] == ["process"]
        assert isinstance(d["process"]["pid"], int)
        assert d["process"]["executable"]
    launchd = next(d for d in docs if d["process"]["name"] == "launchd")
    assert launchd["process"]["pid"] == 1
    safari = next(d for d in docs if d["process"]["name"] == "Safari")
    assert safari["process"]["parent"]["pid"] == 1
    assert safari["user"]["name"] == "analyst"


def test_beacon_process_from_tmp_present():
    docs = normalize_processes(ROWS, HOST)
    assert any("/private/tmp/" in d["process"]["executable"] for d in docs)
