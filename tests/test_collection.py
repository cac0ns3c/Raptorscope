# SPDX-License-Identifier: GPL-3.0-or-later
import json

from raptorscope.collection import load_collection


def test_loads_rows_and_host(tmp_path):
    d = tmp_path / "col"
    d.mkdir()
    (d / "launch_items.json").write_text(json.dumps([{"Path": "/tmp/x.plist"}]))
    (d / "host.json").write_text(json.dumps({"name": "mac-1"}))
    artifacts, host = load_collection(str(d))
    assert host["name"] == "mac-1"
    assert artifacts["launch_items"][0]["Path"] == "/tmp/x.plist"
