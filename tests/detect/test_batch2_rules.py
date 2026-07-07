# SPDX-License-Identifier: GPL-3.0-or-later
"""Batch 2 detections (credential-access, defense-evasion, discovery/exec/exfil,
tcc/quarantine/inventory): each fires on its malicious example and stays silent on
its benign one. Rules authored + adversarially FP-hunted by the detection-engineer
workflow, then proven end-to-end through the real normalizers here."""
import json
import pathlib

import pytest

from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.normalize.inventory import normalize_inventory
from raptorscope.normalize.processes import normalize_processes
from raptorscope.normalize.quarantine import normalize_quarantine
from raptorscope.normalize.tcc import normalize_tcc

RULES = load_rules("detections/sigma")
HOST = {"name": "h", "os": {"type": "macos"}}
NORM = {
    "macos.process": normalize_processes,
    "macos.tcc": normalize_tcc,
    "macos.quarantine": normalize_quarantine,
    "macos.inventory": normalize_inventory,
}
CASES = json.loads((pathlib.Path(__file__).parent / "batch2_cases.json").read_text())
_IDS = [c["filename"] for c in CASES]


def _fired(dataset, row):
    return {a["rule_id"] for a in run_rules(NORM[dataset]([row], HOST), RULES)}


def test_batch_has_all_rules():
    assert len(CASES) == 33
    # every case's rule id + filename is unique
    assert len({c["rule_id"] for c in CASES}) == 33
    assert len(set(_IDS)) == 33


@pytest.mark.parametrize("case", CASES, ids=_IDS)
def test_batch_rule_fires_on_malicious(case):
    assert case["rule_id"] in _fired(case["dataset"], case["malicious_row"]), (
        f"{case['filename']} did not fire on its malicious row"
    )


@pytest.mark.parametrize("case", CASES, ids=_IDS)
def test_batch_rule_silent_on_benign(case):
    assert case["rule_id"] not in _fired(case["dataset"], case["benign_row"]), (
        f"{case['filename']} fired on its benign row"
    )
