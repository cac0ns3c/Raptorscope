# SPDX-License-Identifier: GPL-3.0-or-later
"""Lint the custom Velociraptor artifacts against the contribution guidelines
(https://www.velociraptor-docs.org/dev/contributing-artifacts/). A static proxy
for `velociraptor artifacts verify` (which needs the Velociraptor binary): every
artifact parses, is named after its file, and carries the required metadata —
author, a lead-sentence description, type, a reference, and a darwin-guarded,
named source. Also verifies the profile's custom_vql paths resolve to these files.
"""
import pathlib

import pytest
import yaml

VQL_DIR = pathlib.Path("profile/custom-vql")
ARTIFACTS = sorted(VQL_DIR.glob("*.yaml"))
PROFILE = yaml.safe_load(pathlib.Path("profile/raptorscope-macos.yaml").read_text())


def test_there_are_artifacts():
    assert ARTIFACTS


@pytest.mark.parametrize("path", ARTIFACTS, ids=lambda p: p.name)
def test_artifact_conforms(path):
    art = yaml.safe_load(path.read_text())  # parses (proxy for verify's syntax check)

    # name matches the filename, follows the OS.Namespace.Component pattern
    assert art["name"] == path.stem
    assert art["name"].startswith("MacOS.Raptorscope.")
    assert art["type"] in ("CLIENT", "SERVER")

    # author + reference metadata (contribution guideline)
    assert art.get("author"), f"{path.name}: missing author"
    refs = art.get("reference") or art.get("references")
    assert refs and isinstance(refs, list), f"{path.name}: missing reference list"

    # description: lead sentence, not starting with the discouraged "This artifact"
    desc = (art.get("description") or "").strip()
    assert desc, f"{path.name}: missing description"
    assert not desc.lower().startswith("this artifact"), f"{path.name}: weak lead"

    # named sources, each with a darwin precondition and a query
    sources = art.get("sources") or []
    assert sources, f"{path.name}: no sources"
    for src in sources:
        assert src.get("name"), f"{path.name}: unnamed source"
        assert src.get("query"), f"{path.name}: source has no query"
        assert "darwin" in (src.get("precondition") or ""), (
            f"{path.name}: source lacks a darwin precondition"
        )


def test_profile_custom_vql_paths_resolve_to_named_artifacts():
    # Every profile entry that declares a custom_vql must point to a real file
    # whose artifact `name` equals the entry's `artifact` (the alias key).
    for e in PROFILE["artifacts"]:
        cv = e.get("custom_vql")
        if not cv:
            continue
        p = pathlib.Path(cv)
        assert p.exists(), f"{e['artifact']}: custom_vql path {cv} does not exist"
        assert yaml.safe_load(p.read_text())["name"] == e["artifact"]
