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
import datetime
import json
import os
import pathlib
import plistlib
import shutil
import sqlite3
import subprocess
import tarfile
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


# --------------------------------------------------------------------------- #
# Raw SQLite / plist artifacts (off a disk image — no Velociraptor).           #
# Each reader maps a raw file to the exact row shape an existing normalizer     #
# already consumes, so the ECS mapping + detections are reused as-is.           #
# --------------------------------------------------------------------------- #
_CF_EPOCH = 978307200  # CFAbsoluteTime epoch (2001-01-01 UTC) in unix seconds


def _iso(unix_secs) -> str:
    return datetime.datetime.fromtimestamp(
        float(unix_secs), datetime.timezone.utc
    ).strftime("%Y-%m-%dT%H:%M:%SZ")


def _connect_ro(p: pathlib.Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    return con


def _read_tcc_db(p: pathlib.Path) -> list[dict]:
    """Raw TCC.db ``access`` table -> normalize_tcc rows (fixture/int shape)."""
    con = _connect_ro(p)
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(access)")}
        auth = "auth_value" if "auth_value" in cols else "allowed"
        rows = []
        for r in con.execute("SELECT * FROM access"):
            d = dict(r)
            rows.append({
                "Service": d.get("service"),
                "Client": d.get("client"),
                "ClientType": d.get("client_type"),
                "AuthValue": d.get(auth),
                "LastModified": _iso(d["last_modified"]) if d.get("last_modified") else "",
                "_OSPath": str(p),
            })
        return rows
    finally:
        con.close()


def _read_quarantine_db(p: pathlib.Path) -> list[dict]:
    """Raw QuarantineEventsV2 -> normalize_quarantine rows (LSQuarantine* keys)."""
    import urllib.parse

    con = _connect_ro(p)
    try:
        rows = []
        for r in con.execute("SELECT * FROM LSQuarantineEvent"):
            d = dict(r)
            ts = d.get("LSQuarantineTimeStamp")
            d["LSQuarantineTimeStamp"] = _iso(ts + _CF_EPOCH) if ts else ""
            # There's no on-disk file path in QuarantineEventsV2 — the downloaded
            # file name is the last path segment of the data URL.
            url = d.get("LSQuarantineDataURLString") or ""
            d["Path"] = urllib.parse.urlparse(url).path if url else ""
            rows.append(d)
        return rows
    finally:
        con.close()


def _read_launch_plists(root: pathlib.Path) -> list[dict]:
    """LaunchAgents/LaunchDaemons *.plist -> normalize_launch_items rows."""
    rows = []
    for sub in ("LaunchAgents", "LaunchDaemons"):
        for f in root.rglob(f"{sub}/*.plist"):
            try:
                with open(f, "rb") as fh:
                    pl = dict(plistlib.load(fh))
            except Exception:
                continue
            pl["Path"] = str(f)
            pl["OSPath"] = str(f)
            pl["Mtime"] = _iso(f.stat().st_mtime)
            rows.append(pl)
    return rows


def _find(root: pathlib.Path, name: str):
    hits = list(root.rglob(name))
    return hits[0] if hits else None


def _has_launch_plists(root: pathlib.Path) -> bool:
    return any(
        True
        for s in ("LaunchAgents", "LaunchDaemons")
        for _ in root.rglob(f"{s}/*.plist")
    )


def is_artifact_dir(path: str) -> bool:
    """A directory of raw macOS artifacts (TCC.db / QuarantineEventsV2 / launch plists)."""
    root = pathlib.Path(path)
    if not root.is_dir():
        return False
    return bool(
        _find(root, "TCC.db")
        or _find(root, "*QuarantineEventsV2")
        or _has_launch_plists(root)
    )


def load_artifacts(path: str) -> tuple[dict, dict]:
    """Return ``(artifacts, host)`` for a directory of raw macOS artifacts."""
    root = pathlib.Path(path)
    artifacts: dict[str, list] = {}
    tcc = _find(root, "TCC.db")
    if tcc:
        artifacts["tcc"] = _read_tcc_db(tcc)
    quar = _find(root, "*QuarantineEventsV2")
    if quar:
        artifacts["quarantine"] = _read_quarantine_db(quar)
    plists = _read_launch_plists(root)
    if plists:
        artifacts["launch_items"] = plists
    host = {"name": root.name, "os": {"type": "macos"}}
    return artifacts, host


# --------------------------------------------------------------------------- #
# Bundle drop-and-scan: a whole sysdiagnose / Aftermath collection. Fan out to  #
# every sub-loader (Unified Log + raw artifacts) and merge — best effort, so a  #
# partial/corrupt bundle still yields whatever it can.                          #
# --------------------------------------------------------------------------- #
def is_bundle(path: str) -> bool:
    p = pathlib.Path(path)
    if p.is_file():  # a sysdiagnose tarball
        return ".tar" in p.suffixes or p.suffix in (".tar", ".tgz")
    # a container directory that *holds* a .logarchive (but isn't one itself)
    if p.is_dir() and p.suffix != ".logarchive":
        return any(True for _ in p.rglob("*.logarchive"))
    return False


def load_bundle(path: str) -> tuple[dict, dict]:
    root = pathlib.Path(path)
    tmp = None
    try:
        if root.is_file():
            tmp = tempfile.mkdtemp()
            with tarfile.open(root) as tf:
                tf.extractall(tmp, filter="data")  # safe extraction (py3.12+)
            root = pathlib.Path(tmp)
        artifacts: dict[str, list] = {}
        archive = next(root.rglob("*.logarchive"), None)
        if archive is not None:
            try:
                ul, _ = load_unifiedlog(str(archive))
                artifacts.update(ul)
            except Exception:
                pass  # parser missing/failed — still ingest the raw artifacts
        raw, _ = load_artifacts(str(root))
        artifacts.update(raw)
        host = {"name": pathlib.Path(path).stem, "os": {"type": "macos"}}
        return artifacts, host
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)
