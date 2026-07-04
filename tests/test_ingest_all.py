# SPDX-License-Identifier: GPL-3.0-or-later
"""End-to-end: a full multi-artifact collection normalizes across all datasets."""
import json
import pathlib
import shutil

from raptorscope.cli import ingest, normalize_collection
from raptorscope.collection import enrich_host

FIXTURES = pathlib.Path("fixtures/velociraptor")
# collection json stem -> fixture file
ARTIFACTS = {
    "launch_items": "launch_items.raw.json",
    "login_items": "login_items.raw.json",
    "cron_items": "cron_items.raw.json",
    "config_profiles": "config_profiles.raw.json",
    "btm_items": "btm_items.raw.json",
    "processes": "processes.raw.json",
    "quarantine": "quarantine.raw.json",
    "tcc": "tcc.raw.json",
    "installed_apps": "installed_apps.raw.json",
}


def _build_collection(dst: pathlib.Path) -> int:
    dst.mkdir(parents=True, exist_ok=True)
    total = 0
    for stem, fname in ARTIFACTS.items():
        rows = json.loads((FIXTURES / fname).read_text())
        total += len(rows)
        shutil.copyfile(FIXTURES / fname, dst / f"{stem}.json")
    (dst / "host.json").write_text(
        json.dumps({"name": "mac-victim", "os": {"type": "macos"}})
    )
    return total


def test_enrich_host_defaults_macos():
    assert enrich_host({"name": "h"})["os"]["type"] == "macos"
    assert enrich_host({"host": {"name": "h"}})["name"] == "h"


def test_full_collection_covers_every_dataset(tmp_path):
    col = tmp_path / "col"
    total = _build_collection(col)
    docs = normalize_collection(str(col))
    assert len(docs) == total
    datasets = {d["event"]["dataset"] for d in docs}
    assert datasets == {
        "macos.persistence",
        "macos.process",
        "macos.quarantine",
        "macos.tcc",
        "macos.inventory",
    }
    # every doc carries enriched host context
    assert all(d["host"]["os"]["type"] == "macos" for d in docs)


def test_ingest_dry_run_counts_all(tmp_path):
    col = tmp_path / "col"
    total = _build_collection(col)
    assert ingest(str(col), es_url=None) == total
