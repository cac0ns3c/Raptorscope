# SPDX-License-Identifier: GPL-3.0-or-later
"""The collection profile is a real contract: every artifact it names resolves
to a registered normalizer, and a collection using real Velociraptor artifact
filenames ingests exactly like the stem-named one."""
import json
import pathlib

import yaml

from raptorscope.cli import _NORMALIZERS, ingest, normalize_collection
from raptorscope.collection import ARTIFACT_ALIASES
from raptorscope.detect.pairing import ALL_DATASETS

PROFILE = pathlib.Path("profile/raptorscope-macos.yaml")
FIX = pathlib.Path("fixtures/velociraptor")


def test_profile_artifacts_map_to_normalizers():
    profile = yaml.safe_load(PROFILE.read_text())
    entries = profile["artifacts"]
    assert entries
    for e in entries:
        assert ARTIFACT_ALIASES[e["artifact"]] == e["stem"]
        assert e["stem"] in _NORMALIZERS
        assert e["dataset"] in ALL_DATASETS


def test_real_artifact_filenames_ingest(tmp_path):
    # Build a collection whose files use real Velociraptor artifact names.
    col = tmp_path / "col"
    col.mkdir()
    stem_to_fix = {
        "launch_items": "launch_items.raw.json",
        "login_items": "login_items.raw.json",
        "cron_items": "cron_items.raw.json",
        "config_profiles": "config_profiles.raw.json",
        "btm_items": "btm_items.raw.json",
        "processes": "processes.raw.json",
        "quarantine": "quarantine.raw.json",
        "tcc": "tcc.raw.json",
        "installed_apps": "installed_apps.raw.json",
        "network": "network.raw.json",
    }
    velo_by_stem = {stem: art for art, stem in ARTIFACT_ALIASES.items()}
    for stem, fixture in stem_to_fix.items():
        rows = json.loads((FIX / fixture).read_text())
        (col / f"{velo_by_stem[stem]}.json").write_text(json.dumps(rows))
    (col / "host.json").write_text(
        json.dumps({"name": "mac-victim", "os": {"type": "macos"}})
    )

    docs = normalize_collection(str(col))
    assert len(docs) == 27
    assert {d["event"]["dataset"] for d in docs} == ALL_DATASETS
    assert ingest(str(col), es_url=None) == 27
