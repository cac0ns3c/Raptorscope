# SPDX-License-Identifier: GPL-3.0-or-later
"""Unified Log (raw evidence) → ECS, and its paired detection.

Fixtures mimic real `macos-UnifiedLogs` output shapes (validated 2026-07-07); no
host data is committed.
"""
import json
import pathlib

from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.detect.pairing import ALL_DATASETS, check_pairing
from raptorscope.normalize.unifiedlog import normalize_unifiedlog

ROWS = json.loads(pathlib.Path("fixtures/unifiedlog/tcc_access.raw.json").read_text())
AUTHD = json.loads(pathlib.Path("fixtures/unifiedlog/authd.raw.json").read_text())
HOST = {"name": "h", "os": {"type": "macos"}}
RULES = load_rules("detections/sigma")


def _docs():
    return normalize_unifiedlog(ROWS, HOST)


def test_correlates_authreq_lines_into_one_doc_per_request():
    docs = _docs()
    # 3 msgIDs correlated; the unrelated coreanimation line is ignored.
    assert len(docs) == 3
    assert all(d["event"]["dataset"] == "macos.unifiedlog" for d in docs)
    assert all(d["event"]["action"] == "tcc_access_request" for d in docs)


def test_extracts_service_client_and_allowed():
    by = {d["raptorscope"]["tcc"]["client"]: d["raptorscope"]["tcc"] for d in _docs()}
    agent = by["/Users/analyst/.hidden/agent"]
    assert agent["service"] == "kTCCServiceListenEvent"
    assert agent["client_type"] == "path"      # subject is an absolute path
    assert agent["allowed"] is True            # authValue=2
    term = by["com.apple.Terminal"]
    assert term["client_type"] == "bundle_id"
    assert term["service"] == "kTCCServiceScreenCapture"


def test_path_subject_becomes_process_executable():
    agent = next(d for d in _docs() if d["raptorscope"]["tcc"]["client_type"] == "path")
    assert agent["process"]["executable"] == "/Users/analyst/.hidden/agent"


def test_sensitive_request_detection_fires_only_on_non_apple_sensitive():
    alerts = run_rules(_docs(), RULES)
    hits = [a for a in alerts if "sensitive TCC service" in a["title"].lower()
            or "sensitive tcc" in a["title"].lower()]
    # Exactly one: the non-Apple path client requesting ListenEvent.
    assert len(hits) == 1
    ev = hits[0]["evidence"]
    assert ev["raptorscope.tcc.client"] == "/Users/analyst/.hidden/agent"
    assert ev["raptorscope.tcc.service"] == "kTCCServiceListenEvent"


def test_apple_client_and_nonsensitive_service_do_not_fire():
    fired_clients = {
        a["evidence"].get("raptorscope.tcc.client")
        for a in run_rules(_docs(), RULES)
        if "tcc" in a["title"].lower()
    }
    assert "com.apple.Terminal" not in fired_clients      # Apple client filtered
    assert "com.acme.contacts" not in fired_clients       # AddressBook not sensitive


def test_authd_correlates_right_grant_to_requesting_process():
    docs = normalize_unifiedlog(AUTHD, HOST)
    assert len(docs) == 3  # three "granting right" lines
    assert all(d["event"]["action"] == "authorization_right" for d in docs)
    by = {(d["process"]["executable"], d["raptorscope"]["unifiedlog"]["right"]) for d in docs}
    # process joined to right by engine id
    assert ("/Users/analyst/Downloads/Installer.app/Contents/MacOS/Installer",
            "com.apple.ServiceManagement.daemons.modify") in by
    assert ("/usr/libexec/mdmclient",
            "com.apple.ServiceManagement.daemons.modify") in by


def test_authd_detection_fires_only_on_nonsystem_sensitive_grant():
    alerts = run_rules(normalize_unifiedlog(AUTHD, HOST), RULES)
    hits = [a for a in alerts if "authorization right" in a["title"].lower()]
    # Only the user-space Installer granted daemons.modify — mdmclient (system)
    # and print.admin (not sensitive) are excluded.
    assert len(hits) == 1
    assert "Installer" in hits[0]["evidence"]["process.executable"]
    assert hits[0]["evidence"]["raptorscope.unifiedlog.right"] == \
        "com.apple.ServiceManagement.daemons.modify"


def test_pairing_guard_clean_with_new_dataset():
    assert check_pairing(ALL_DATASETS, "detections/sigma") == []
