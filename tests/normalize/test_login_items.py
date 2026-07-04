# SPDX-License-Identifier: GPL-3.0-or-later
import json
import pathlib

from raptorscope.normalize.login_items import normalize_login_items

ROWS = json.loads(
    pathlib.Path("fixtures/velociraptor/login_items.raw.json").read_text()
)
HOST = {"name": "mac-victim", "os": {"type": "macos"}}


def test_maps_each_row_to_one_ecs_doc():
    docs = normalize_login_items(ROWS, HOST)
    assert len(docs) == len(ROWS)


def test_persistence_type_is_login_item():
    docs = normalize_login_items(ROWS, HOST)
    for d in docs:
        assert d["event"]["dataset"] == "macos.persistence"
        assert d["raptorscope"]["persistence"]["type"] == "login_item"
        assert d["file"]["path"]


def test_user_and_executable_mapped():
    docs = normalize_login_items(ROWS, HOST)
    d = docs[0]
    assert d["user"]["name"] == "analyst"
    assert d["process"]["executable"].endswith("Dropbox")


def test_suspicious_login_item_present():
    docs = normalize_login_items(ROWS, HOST)
    assert any("/Users/Shared/" in d["file"]["path"] for d in docs)
