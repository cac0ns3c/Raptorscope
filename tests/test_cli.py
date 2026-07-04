# SPDX-License-Identifier: GPL-3.0-or-later
import json

from raptorscope.cli import ingest


def test_ingest_dry_run_counts(tmp_path, capsys):
    d = tmp_path / "col"
    d.mkdir()
    (d / "launch_items.json").write_text(
        json.dumps([{"Path": "/tmp/x.plist", "Label": "evil"}])
    )
    (d / "host.json").write_text(
        json.dumps({"name": "mac-1", "os": {"type": "macos"}})
    )
    n = ingest(str(d), es_url=None)
    assert n == 1
