# SPDX-License-Identifier: GPL-3.0-or-later
"""The added detections fire on the sample fixtures and stay paired."""
import json
import pathlib

from raptorscope.detect.convert import convert_rule
from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.detect.pairing import ALL_DATASETS, check_pairing
from raptorscope.normalize.launch_items import normalize_launch_items
from raptorscope.normalize.processes import normalize_processes
from raptorscope.normalize.quarantine import normalize_quarantine
from raptorscope.normalize.tcc import normalize_tcc

FIX = pathlib.Path("fixtures/velociraptor")
HOST = {"name": "h", "os": {"type": "macos"}}
RULES = load_rules("detections/sigma")


def _rows(name):
    return json.loads((FIX / name).read_text())


def _titles(docs):
    return {a["title"] for a in run_rules(docs, RULES)}


def test_all_new_rules_convert():
    for stem in [
        "macos_process_network_command",
        "macos_quarantine_cleartext_http",
        "macos_tcc_path_client_grant",
        "macos_persistence_shell_download",
    ]:
        q = convert_rule(f"detections/sigma/{stem}.yml")
        assert q  # non-empty Lucene query


def test_pairing_still_clean():
    assert check_pairing(ALL_DATASETS, "detections/sigma") == []


def test_process_network_command_fires():
    docs = normalize_processes(_rows("processes.raw.json"), HOST)
    assert any("network" in t.lower() for t in _titles(docs))


def test_quarantine_cleartext_http_fires():
    docs = normalize_quarantine(_rows("quarantine.raw.json"), HOST)
    assert any("cleartext" in t.lower() or "http" in t.lower() for t in _titles(docs))


def test_tcc_path_client_fires():
    docs = normalize_tcc(_rows("tcc.raw.json"), HOST)
    assert any("path-based" in t.lower() or "path client" in t.lower() for t in _titles(docs))


def test_persistence_shell_download_fires():
    docs = normalize_launch_items(_rows("launch_items.raw.json"), HOST)
    assert any("shell" in t.lower() or "download" in t.lower() for t in _titles(docs))
