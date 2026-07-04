# SPDX-License-Identifier: GPL-3.0-or-later
import json
import pathlib

from raptorscope.normalize.tcc import normalize_tcc

ROWS = json.loads(pathlib.Path("fixtures/velociraptor/tcc.raw.json").read_text())
HOST = {"name": "mac-victim", "os": {"type": "macos"}}


def test_maps_each_row_to_one_ecs_doc():
    docs = normalize_tcc(ROWS, HOST)
    assert len(docs) == len(ROWS)


def test_tcc_dataset_and_fields():
    docs = normalize_tcc(ROWS, HOST)
    for d in docs:
        assert d["event"]["dataset"] == "macos.tcc"
        assert d["raptorscope"]["tcc"]["service"]
        assert isinstance(d["raptorscope"]["tcc"]["allowed"], bool)


def test_authvalue_maps_to_allowed_bool():
    docs = normalize_tcc(ROWS, HOST)
    assert all(d["raptorscope"]["tcc"]["allowed"] is True for d in docs)


def test_path_client_becomes_executable():
    docs = normalize_tcc(ROWS, HOST)
    a11y = next(
        d for d in docs if d["raptorscope"]["tcc"]["service"] == "kTCCServiceAccessibility"
    )
    assert a11y["process"]["executable"] == "/Users/Shared/.helper/agent"
