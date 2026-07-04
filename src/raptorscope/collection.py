# SPDX-License-Identifier: GPL-3.0-or-later
"""Load a Velociraptor collection (directory or zip) into rows + host."""
import json
import pathlib
import tempfile
import zipfile


def _load_dir(root: pathlib.Path) -> tuple[dict, dict]:
    host = {}
    if (root / "host.json").exists():
        host = json.loads((root / "host.json").read_text())
    artifacts = {}
    for f in root.glob("*.json"):
        if f.name == "host.json":
            continue
        artifacts[f.stem] = json.loads(f.read_text())
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
