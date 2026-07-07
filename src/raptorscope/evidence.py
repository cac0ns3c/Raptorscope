# SPDX-License-Identifier: GPL-3.0-or-later
"""Load *raw* macOS evidence (no Velociraptor) into rows + host.

Phase 1: Apple Unified Logs. A ``.logarchive`` is parsed offline by the
``macos-UnifiedLogs`` iterator (Rust) to JSONL, filtered to the predicates of
interest, and returned in the same ``(artifacts, host)`` shape as
``collection.load_collection`` so the rest of the pipeline is untouched.

The parser binary is located via ``$RAPTORSCOPE_UNIFIEDLOG_BIN``, else
``tools/unifiedlog_iterator`` (dev), else ``unifiedlog_iterator`` on PATH (the
Docker image bakes it in).
"""
import json
import os
import pathlib
import shutil
import subprocess
import tempfile

# Unified Log subsystems we ingest (selection, not firehose — a .logarchive is
# millions of lines): TCC access decisions + authorization-right grants.
PREDICATE_SUBSYSTEMS = ("com.apple.TCC", "com.apple.Authorization")


def _parser_bin() -> str:
    env = os.environ.get("RAPTORSCOPE_UNIFIEDLOG_BIN")
    if env:
        return env
    local = pathlib.Path("tools/unifiedlog_iterator")
    if local.exists():
        return str(local)
    found = shutil.which("unifiedlog_iterator")
    if not found:
        raise FileNotFoundError(
            "unifiedlog_iterator not found — set RAPTORSCOPE_UNIFIEDLOG_BIN, put it "
            "at tools/unifiedlog_iterator, or on PATH (see docs/plans)."
        )
    return found


def is_logarchive(path: str) -> bool:
    """A ``.logarchive`` is a directory (by suffix, or containing a tracev3 store)."""
    p = pathlib.Path(path)
    if p.suffix == ".logarchive":
        return True
    return p.is_dir() and (p / "logdata.LiveData.tracev3").exists()


def _run_parser(archive: str) -> list[dict]:
    """Parse a .logarchive to JSONL and return the rows for our predicates."""
    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "ul.jsonl"
        subprocess.run(
            [_parser_bin(), "--mode", "log-archive", "--input", archive,
             "--format", "jsonl", "--output", str(out)],
            check=True, capture_output=True,
        )
        rows = []
        with open(out) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("subsystem") in PREDICATE_SUBSYSTEMS:
                    rows.append(r)
        return rows


def load_unifiedlog(path: str) -> tuple[dict, dict]:
    """Return ``(artifacts, host)`` for a raw .logarchive.

    ``artifacts`` maps the ``unifiedlog`` stem -> filtered rows, matching the
    ``collection.load_collection`` contract so ``normalize_collection`` can treat
    both inputs identically.
    """
    rows = _run_parser(path)
    host = {"name": pathlib.Path(path).stem, "os": {"type": "macos"}}
    return {"unifiedlog": rows}, host
