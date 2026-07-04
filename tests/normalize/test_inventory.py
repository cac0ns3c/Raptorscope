# SPDX-License-Identifier: GPL-3.0-or-later
import json
import pathlib

from raptorscope.normalize.inventory import normalize_inventory

ROWS = json.loads(
    pathlib.Path("fixtures/velociraptor/installed_apps.raw.json").read_text()
)
HOST = {"name": "mac-victim", "os": {"type": "macos"}}


def test_maps_each_row_to_one_ecs_doc():
    docs = normalize_inventory(ROWS, HOST)
    assert len(docs) == len(ROWS)


def test_inventory_dataset_and_fields():
    docs = normalize_inventory(ROWS, HOST)
    for d in docs:
        assert d["event"]["dataset"] == "macos.inventory"
        assert d["event"]["category"] == ["package"]
        assert d["raptorscope"]["app"]["name"]
        assert d["file"]["path"]


def test_signed_flag_and_outside_applications():
    docs = normalize_inventory(ROWS, HOST)
    by_name = {d["raptorscope"]["app"]["name"]: d for d in docs}
    assert by_name["Slack"]["raptorscope"]["app"]["signed"] is True
    updater = by_name["Updater"]
    assert updater["raptorscope"]["app"]["signed"] is False
    assert not updater["file"]["path"].startswith("/Applications/")
