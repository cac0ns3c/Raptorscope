# SPDX-License-Identifier: GPL-3.0-or-later
"""Load a Velociraptor collection (directory or zip) into rows + host."""
import json
import pathlib
import tempfile
import zipfile

# Velociraptor built-in artifact name -> collection stem (the key the CLI's
# _NORMALIZERS registry uses). Lets a real collection zip — whose result files
# are named by artifact — ingest without renaming. See profile/raptorscope-macos.yaml.
ARTIFACT_ALIASES = {
    # Placeholder names used by the synthetic fixtures / sample collection.
    "MacOS.System.LaunchServices": "launch_items",
    "MacOS.System.LoginItems": "login_items",
    "MacOS.System.Crontab": "cron_items",
    "MacOS.System.Profiles": "config_profiles",
    "MacOS.System.BackgroundTaskManagement": "btm_items",
    "MacOS.System.Processes": "processes",
    # Real Velociraptor built-in artifact names (confirmed against the docs; see
    # docs/spikes/2026-07-04-real-velociraptor-validation.md). The persistence
    # family really comes from the single MacOS.Detection.Autoruns artifact whose
    # per-source columns differ from the synthetic fixtures — that mapper still
    # needs rework, tracked in the spike note.
    "MacOS.Sys.Pslist": "processes",
    "MacOS.System.QuarantineEvents": "quarantine",
    "MacOS.System.TCC": "tcc",
    "MacOS.System.Packages": "installed_apps",
    # The whole persistence family really comes from one Autoruns artifact.
    "MacOS.Detection.Autoruns": "autoruns",
    # Custom VQL artifacts (profile/custom-vql/) for what has no built-in.
    "MacOS.Raptorscope.ConfigProfiles": "config_profiles",
    "MacOS.Raptorscope.BTM": "btm_items",
    # Signature-enriched processes so trusted:false detections work on real data.
    "MacOS.Raptorscope.SignedProcesses": "processes",
    # Signature-enriched Autoruns for untrusted-persistence detections.
    "MacOS.Raptorscope.SignedAutoruns": "autoruns",
    # Host network connections (listeners + established) with owning process.
    "MacOS.Raptorscope.Netstat": "network",
}


def canonical_artifact(name: str) -> str:
    """Resolve a collection file stem to its canonical artifact stem."""
    return ARTIFACT_ALIASES.get(name, name)


def enrich_host(raw: dict) -> dict:
    """Return the ECS ``host.*`` object for a collection's ``host.json``.

    Accepts either a flat host dict (``{"name": ..., "os": {...}}``) or a
    wrapped one carrying sibling context (``{"host": {...}, "user": {...}}``),
    and defaults ``host.os.type`` to ``macos`` (raptorscope is macOS-only).
    """
    host = dict(raw.get("host", raw)) if isinstance(raw, dict) else {}
    os_ctx = dict(host.get("os") or {})
    os_ctx.setdefault("type", "macos")
    host["os"] = os_ctx
    return host


def _load_dir(root: pathlib.Path) -> tuple[dict, dict]:
    host = {}
    if (root / "host.json").exists():
        host = json.loads((root / "host.json").read_text())
    artifacts = {}
    for f in root.glob("*.json"):
        if f.name == "host.json":
            continue
        artifacts[canonical_artifact(f.stem)] = json.loads(f.read_text())
    return artifacts, host


def load_collection(path: str) -> tuple[dict, dict]:
    """Return ``(artifacts, host)`` for a collection directory or zip.

    ``artifacts`` maps artifact name (json file stem) -> list of rows.
    """
    root = pathlib.Path(path)
    if root.is_file() and zipfile.is_zipfile(root):
        with tempfile.TemporaryDirectory() as tmp:
            with zipfile.ZipFile(root) as zf:
                zf.extractall(tmp)
            return _load_dir(pathlib.Path(tmp))
    return _load_dir(root)
