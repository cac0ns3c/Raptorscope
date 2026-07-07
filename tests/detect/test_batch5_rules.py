# SPDX-License-Identifier: GPL-3.0-or-later
"""Batch 5 detections: MITRE-map-driven gap fill — Discovery, Impact,
Exfiltration, Lateral Movement, and the remaining Defense-Evasion / Persistence /
Credential-Access / C2 gaps. Each fires on its malicious example and stays silent
on its benign one. Authored + FP-hunted by the detection-engineer workflow."""
import json
import pathlib

import pytest

from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.normalize.inventory import normalize_inventory
from raptorscope.normalize.processes import normalize_processes

RULES = load_rules("detections/sigma")
HOST = {"name": "h", "os": {"type": "macos"}}
NORM = {"processes": normalize_processes, "inventory": normalize_inventory}
CASES = json.loads((pathlib.Path(__file__).parent / "batch5_cases.json").read_text())
_IDS = [c["filename"] for c in CASES]


def _fired(normalizer, row):
    return {a["rule_id"] for a in run_rules(NORM[normalizer]([row], HOST), RULES)}


def test_batch5_has_all_rules():
    assert len(CASES) == 38
    assert len({c["rule_id"] for c in CASES}) == 38
    assert len(set(_IDS)) == 38


@pytest.mark.parametrize("case", CASES, ids=_IDS)
def test_batch5_rule_fires_on_malicious(case):
    assert case["rule_id"] in _fired(case["normalizer"], case["malicious_row"]), (
        f"{case['filename']} did not fire on its malicious row"
    )


@pytest.mark.parametrize("case", CASES, ids=_IDS)
def test_batch5_rule_silent_on_benign(case):
    assert case["rule_id"] not in _fired(case["normalizer"], case["benign_row"]), (
        f"{case['filename']} fired on its benign row"
    )
