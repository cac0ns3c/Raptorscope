# SPDX-License-Identifier: GPL-3.0-or-later
import json
import pathlib

from raptorscope.normalize.launch_items import normalize_launch_items

ROWS = json.loads(
    pathlib.Path("fixtures/velociraptor/launch_items.raw.json").read_text()
)
HOST = {"name": "mac-victim", "os": {"type": "macos"}}


def test_maps_each_row_to_one_ecs_doc():
    docs = normalize_launch_items(ROWS, HOST)
    assert len(docs) == len(ROWS)


def test_persistence_type_from_path():
    docs = normalize_launch_items(ROWS, HOST)
    types = {d["raptorscope"]["persistence"]["type"] for d in docs}
    assert types <= {"launch_agent", "launch_daemon"}
    for d in docs:
        assert d["event"]["dataset"] == "macos.persistence"
        assert d["host"]["os"]["type"] == "macos"
        assert d["file"]["path"]  # plist path present


def test_program_becomes_process_executable():
    docs = normalize_launch_items(ROWS, HOST)
    assert any(d.get("process", {}).get("executable") for d in docs)


def test_program_arguments_join_into_command_line():
    docs = normalize_launch_items(ROWS, HOST)
    keystone = next(
        d for d in docs
        if d["raptorscope"]["persistence"]["label"] == "com.google.keystone.agent"
    )
    assert "-runMode" in keystone["process"]["command_line"]


def test_code_signature_mapped_when_present():
    docs = normalize_launch_items(ROWS, HOST)
    signed = next(
        d for d in docs
        if d["raptorscope"]["persistence"]["label"] == "com.apple.softwareupdated"
    )
    assert signed["process"]["code_signature"]["trusted"] is True
