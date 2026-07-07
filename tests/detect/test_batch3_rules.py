# SPDX-License-Identifier: GPL-3.0-or-later
"""Batch 3 detections (persistence across launchd/cron/BTM/login-items, and
network C2/backdoor/tunnel). Each case names the normalizer that feeds its dataset
(macos.persistence has five feeders), fires on its malicious example, and stays
silent on its benign one. Authored + FP-hunted by the detection-engineer workflow."""
import json
import pathlib

import pytest

from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.normalize.btm import normalize_btm
from raptorscope.normalize.config_profiles import normalize_config_profiles
from raptorscope.normalize.cron import normalize_cron
from raptorscope.normalize.launch_items import normalize_launch_items
from raptorscope.normalize.login_items import normalize_login_items
from raptorscope.normalize.network import normalize_network

RULES = load_rules("detections/sigma")
HOST = {"name": "h", "os": {"type": "macos"}}
NORM = {
    "launch_items": normalize_launch_items,
    "cron": normalize_cron,
    "btm": normalize_btm,
    "config_profiles": normalize_config_profiles,
    "login_items": normalize_login_items,
    "network": normalize_network,
}
CASES = json.loads((pathlib.Path(__file__).parent / "batch3_cases.json").read_text())
_IDS = [c["filename"] for c in CASES]


def _fired(normalizer, row):
    return {a["rule_id"] for a in run_rules(NORM[normalizer]([row], HOST), RULES)}


def test_batch3_has_all_rules():
    assert len(CASES) == 16
    assert len({c["rule_id"] for c in CASES}) == 16
    assert len(set(_IDS)) == 16


@pytest.mark.parametrize("case", CASES, ids=_IDS)
def test_batch3_rule_fires_on_malicious(case):
    assert case["rule_id"] in _fired(case["normalizer"], case["malicious_row"]), (
        f"{case['filename']} did not fire on its malicious row"
    )


@pytest.mark.parametrize("case", CASES, ids=_IDS)
def test_batch3_rule_silent_on_benign(case):
    assert case["rule_id"] not in _fired(case["normalizer"], case["benign_row"]), (
        f"{case['filename']} fired on its benign row"
    )
