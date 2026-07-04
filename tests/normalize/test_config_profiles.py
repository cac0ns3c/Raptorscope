# SPDX-License-Identifier: GPL-3.0-or-later
import json
import pathlib

from raptorscope.normalize.config_profiles import normalize_config_profiles

ROWS = json.loads(
    pathlib.Path("fixtures/velociraptor/config_profiles.raw.json").read_text()
)
HOST = {"name": "mac-victim", "os": {"type": "macos"}}


def test_maps_each_row_to_one_ecs_doc():
    docs = normalize_config_profiles(ROWS, HOST)
    assert len(docs) == len(ROWS)


def test_persistence_type_and_payload():
    docs = normalize_config_profiles(ROWS, HOST)
    for d in docs:
        assert d["event"]["dataset"] == "macos.persistence"
        assert d["raptorscope"]["persistence"]["type"] == "config_profile"
        assert d["raptorscope"]["persistence"]["payload_type"]


def test_signed_flag_reflects_signer():
    docs = normalize_config_profiles(ROWS, HOST)
    signed = {
        d["raptorscope"]["persistence"]["label"]: d["raptorscope"]["persistence"]["signed"]
        for d in docs
    }
    assert signed["com.apple.mdm.corp.wifi"] is True
    assert signed["com.systemhelper.support"] is False
