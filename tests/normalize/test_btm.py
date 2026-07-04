# SPDX-License-Identifier: GPL-3.0-or-later
import json
import pathlib

from raptorscope.normalize.btm import normalize_btm

ROWS = json.loads(pathlib.Path("fixtures/velociraptor/btm_items.raw.json").read_text())
HOST = {"name": "mac-victim", "os": {"type": "macos"}}


def test_maps_each_row_to_one_ecs_doc():
    docs = normalize_btm(ROWS, HOST)
    assert len(docs) == len(ROWS)


def test_persistence_type_and_btm_fields():
    docs = normalize_btm(ROWS, HOST)
    for d in docs:
        assert d["event"]["dataset"] == "macos.persistence"
        assert d["raptorscope"]["persistence"]["type"] == "btm"
        assert d["raptorscope"]["persistence"]["btm_type"] in {"agent", "daemon", "login_item"}
        assert d["process"]["executable"]


def test_malicious_btm_in_tmp_present():
    docs = normalize_btm(ROWS, HOST)
    assert any("/private/tmp/" in d["process"]["executable"] for d in docs)
