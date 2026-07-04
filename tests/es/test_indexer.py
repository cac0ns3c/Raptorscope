# SPDX-License-Identifier: GPL-3.0-or-later
from unittest.mock import patch

from raptorscope.es.indexer import bulk_index
from raptorscope.es.template import INDEX_PATTERN, INDEX_TEMPLATE


def test_template_targets_pattern():
    assert INDEX_PATTERN == "raptorscope-*"
    assert "template" in INDEX_TEMPLATE


def test_put_index_template_applies_ecs_mappings():
    from unittest.mock import MagicMock

    from raptorscope.es.template import put_index_template

    client = MagicMock()
    put_index_template(client)
    client.indices.put_index_template.assert_called_once()
    kwargs = client.indices.put_index_template.call_args.kwargs
    assert kwargs["name"] == "raptorscope"
    assert kwargs["index_patterns"] == ["raptorscope-*"]
    assert "mappings" in kwargs["template"]


def test_bulk_index_sends_all_docs():
    docs = [{"@timestamp": "t", "event": {"dataset": "macos.persistence"}}]
    with patch("raptorscope.es.indexer.helpers.bulk", return_value=(1, [])) as m:
        n = bulk_index(client=object(), index="raptorscope-persistence", docs=docs)
    assert n == 1
    actions = list(m.call_args.args[1])
    assert actions[0]["_index"] == "raptorscope-persistence"
