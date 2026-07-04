# SPDX-License-Identifier: GPL-3.0-or-later
"""Every rule maps to a MITRE technique, and known-benign rows fire nothing
while known-malicious rows fire something (hit + benign coverage per dataset)."""
import json
import pathlib
import re

from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.normalize.btm import normalize_btm
from raptorscope.normalize.config_profiles import normalize_config_profiles
from raptorscope.normalize.cron import normalize_cron
from raptorscope.normalize.inventory import normalize_inventory
from raptorscope.normalize.launch_items import normalize_launch_items
from raptorscope.normalize.login_items import normalize_login_items
from raptorscope.normalize.processes import normalize_processes
from raptorscope.normalize.quarantine import normalize_quarantine
from raptorscope.normalize.tcc import normalize_tcc

FIX = pathlib.Path("fixtures/velociraptor")
HOST = {"name": "h", "os": {"type": "macos"}}
RULES = load_rules("detections/sigma")
_TECH = re.compile(r"attack\.t\d{4}", re.IGNORECASE)


def _rows(name):
    return json.loads((FIX / name).read_text())


# (normalizer, fixture, benign row indices, malicious row indices)
CASES = [
    (normalize_launch_items, "launch_items.raw.json", [0, 1], [2, 3]),
    (normalize_login_items, "login_items.raw.json", [0], [1]),
    (normalize_cron, "cron_items.raw.json", [0], [1]),
    (normalize_config_profiles, "config_profiles.raw.json", [0], [1]),
    (normalize_btm, "btm_items.raw.json", [0], [1]),
    (normalize_processes, "processes.raw.json", [0, 1], [2]),
    (normalize_quarantine, "quarantine.raw.json", [0], [1]),
    (normalize_tcc, "tcc.raw.json", [0, 1], [2]),
    (normalize_inventory, "installed_apps.raw.json", [0], [1]),
]


def test_every_rule_has_a_mitre_technique():
    assert RULES
    for r in RULES:
        assert any(_TECH.search(t) for t in r.tags), f"{r.id} has no MITRE technique"


def test_benign_rows_fire_nothing():
    for fn, fixture, benign_idx, _ in CASES:
        rows = _rows(fixture)
        benign = fn([rows[i] for i in benign_idx], HOST)
        alerts = run_rules(benign, RULES)
        assert alerts == [], f"benign {fixture} unexpectedly fired: {alerts}"


def test_malicious_rows_fire_something():
    for fn, fixture, _, mal_idx in CASES:
        rows = _rows(fixture)
        mal = fn([rows[i] for i in mal_idx], HOST)
        assert run_rules(mal, RULES), f"malicious {fixture} fired nothing"
