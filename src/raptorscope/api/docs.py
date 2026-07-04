# SPDX-License-Identifier: GPL-3.0-or-later
"""Curated, user-facing documentation surfaced through the API / GUI.

Only the docs that help someone *use* Raptorscope are listed here — the internal
design spec, phase plans, and spike notes are deliberately excluded.
"""
import pathlib

# Repo root: src/raptorscope/api/docs.py -> parents[3].
DOCS_ROOT = pathlib.Path(__file__).resolve().parents[3]

MEANINGFUL_DOCS = [
    {"id": "readme", "title": "Overview", "path": "README.md"},
    {"id": "install", "title": "Install", "path": "docs/INSTALL.md"},
    {"id": "demo", "title": "Demo walkthrough", "path": "docs/DEMO.md"},
    {"id": "kibana", "title": "Using Kibana", "path": "docs/KIBANA.md"},
    {"id": "profile", "title": "Collection profile", "path": "profile/README.md"},
]

_BY_ID = {d["id"]: d for d in MEANINGFUL_DOCS}


def list_docs() -> list[dict]:
    """The docs that actually exist on disk, in menu order."""
    return [
        {"id": d["id"], "title": d["title"]}
        for d in MEANINGFUL_DOCS
        if (DOCS_ROOT / d["path"]).is_file()
    ]


def get_doc(doc_id: str) -> dict | None:
    """Return ``{id, title, markdown}`` for a known doc, or ``None``."""
    meta = _BY_ID.get(doc_id)
    if not meta:
        return None
    path = DOCS_ROOT / meta["path"]
    if not path.is_file():
        return None
    return {"id": doc_id, "title": meta["title"], "markdown": path.read_text()}
