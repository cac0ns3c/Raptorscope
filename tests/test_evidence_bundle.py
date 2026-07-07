# SPDX-License-Identifier: GPL-3.0-or-later
"""Bundle drop-and-scan: a sysdiagnose dir/tarball fans out to the sub-loaders.
The unified-log step is pointed at a bogus parser so it fails fast — proving a
partial bundle still ingests its raw artifacts."""
import sqlite3
import tarfile

from raptorscope.cli import normalize_collection
from raptorscope.detect.evaluate import load_rules, run_rules
from raptorscope.evidence import is_bundle

RULES = load_rules("detections/sigma")


def _make_tcc(root):
    con = sqlite3.connect(root / "TCC.db")
    con.execute(
        "CREATE TABLE access (service TEXT, client TEXT, client_type INTEGER, "
        "auth_value INTEGER, last_modified INTEGER)"
    )
    con.execute(
        "INSERT INTO access VALUES (?,?,?,?,?)",
        ("kTCCServiceAccessibility", "/Users/Shared/.x/agent", 1, 2, 1751000000),
    )
    con.commit()
    con.close()


def test_bundle_dir_with_unusable_logarchive_still_ingests_artifacts(tmp_path, monkeypatch):
    monkeypatch.setenv("RAPTORSCOPE_UNIFIEDLOG_BIN", "/nonexistent/ul")
    arch = tmp_path / "system_logs.logarchive"
    arch.mkdir()
    (arch / "dummy").write_text("not a real tracev3")
    _make_tcc(tmp_path)

    assert is_bundle(str(tmp_path)) is True
    docs = normalize_collection(str(tmp_path))
    # unified log skipped (bogus parser), raw TCC.db still ingested + detected
    assert any(d["event"]["dataset"] == "macos.tcc" for d in docs)
    titles = " ".join(a["title"].lower() for a in run_rules(docs, RULES))
    assert "path-based" in titles or "path client" in titles


def test_sysdiagnose_tarball_is_a_bundle(tmp_path, monkeypatch):
    monkeypatch.setenv("RAPTORSCOPE_UNIFIEDLOG_BIN", "/nonexistent/ul")
    inner = tmp_path / "sysdiagnose_2026"
    inner.mkdir()
    _make_tcc(inner)
    tarp = tmp_path / "sysdiagnose.tar.gz"
    with tarfile.open(tarp, "w:gz") as tf:
        tf.add(inner, arcname="sysdiagnose_2026")

    assert is_bundle(str(tarp)) is True
    docs = normalize_collection(str(tarp))
    assert any(d["event"]["dataset"] == "macos.tcc" for d in docs)
