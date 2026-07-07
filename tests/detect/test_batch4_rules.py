# SPDX-License-Identifier: GPL-3.0-or-later
"""Batch 4 detections: Unified-Log (TCC path-clients + dangerous authorization
rights, reconstructed from multi-line correlated log rows) and process
privilege-escalation / lateral-movement. A unified-log case's row is a *list* of
message lines; a process case's row is a single artifact row."""
import json
import pathlib

import pytest

from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.normalize.processes import normalize_processes
from raptorscope.normalize.unifiedlog import normalize_unifiedlog

RULES = load_rules("detections/sigma")
HOST = {"name": "h", "os": {"type": "macos"}}
NORM = {"processes": normalize_processes, "unifiedlog": normalize_unifiedlog}
CASES = json.loads((pathlib.Path(__file__).parent / "batch4_cases.json").read_text())
_IDS = [c["filename"] for c in CASES]


def _fired(normalizer, row):
    # Unified-log events are reconstructed from several correlated log lines, so a
    # case row may be a list; process rows are single dicts.
    rows = row if isinstance(row, list) else [row]
    return {a["rule_id"] for a in run_rules(NORM[normalizer](rows, HOST), RULES)}


def test_batch4_has_all_rules():
    assert len(CASES) == 13
    assert len({c["rule_id"] for c in CASES}) == 13
    assert len(set(_IDS)) == 13


@pytest.mark.parametrize("case", CASES, ids=_IDS)
def test_batch4_rule_fires_on_malicious(case):
    assert case["rule_id"] in _fired(case["normalizer"], case["malicious_row"]), (
        f"{case['filename']} did not fire on its malicious row"
    )


@pytest.mark.parametrize("case", CASES, ids=_IDS)
def test_batch4_rule_silent_on_benign(case):
    assert case["rule_id"] not in _fired(case["normalizer"], case["benign_row"]), (
        f"{case['filename']} fired on its benign row"
    )
