# SPDX-License-Identifier: GPL-3.0-or-later
from raptorscope.detect.convert import convert_rule


def test_rule_converts_to_elastic_query():
    q = convert_rule("detections/sigma/macos_persistence_suspicious_path.yml")
    assert "file.path" in q  # selects on the normalized ECS field


def test_login_item_rule_converts():
    q = convert_rule("detections/sigma/macos_persistence_login_item_suspicious.yml")
    assert "raptorscope.persistence.type" in q
    assert "file.path" in q
