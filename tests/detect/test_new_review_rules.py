# SPDX-License-Identifier: GPL-3.0-or-later
"""The 13 review-proposed detections: each fires on its malicious example row and
stays silent on its benign one (cases authored + adversarially verified by the
new-detections workflow, then normalized through the real pipeline here)."""
import json
import pathlib

import pytest

from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.normalize.autoruns import normalize_autoruns
from raptorscope.normalize.inventory import normalize_inventory
from raptorscope.normalize.processes import normalize_processes
from raptorscope.normalize.quarantine import normalize_quarantine
from raptorscope.normalize.tcc import normalize_tcc

RULES = load_rules("detections/sigma")
HOST = {"name": "h", "os": {"type": "macos"}}
NORM = {
    "macos.process": normalize_processes,
    "macos.persistence": normalize_autoruns,
    "macos.tcc": normalize_tcc,
    "macos.quarantine": normalize_quarantine,
    "macos.inventory": normalize_inventory,
}
CASES = json.loads((pathlib.Path(__file__).parent / "new_rules_cases.json").read_text())
_IDS = [c["filename"] for c in CASES]


def _fired_ids(dataset, row):
    docs = NORM[dataset]([row], HOST)
    return {a["rule_id"] for a in run_rules(docs, RULES)}


def test_have_thirteen_new_rules():
    assert len(CASES) == 13


@pytest.mark.parametrize("case", CASES, ids=_IDS)
def test_new_rule_fires_on_malicious(case):
    assert case["rule_id"] in _fired_ids(case["dataset"], case["malicious_row"]), (
        f"{case['filename']} did not fire on its malicious row"
    )


@pytest.mark.parametrize("case", CASES, ids=_IDS)
def test_new_rule_silent_on_benign(case):
    assert case["rule_id"] not in _fired_ids(case["dataset"], case["benign_row"]), (
        f"{case['filename']} fired on its benign row"
    )
