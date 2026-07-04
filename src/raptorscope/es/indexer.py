# SPDX-License-Identifier: GPL-3.0-or-later
"""Thin bulk indexer over the Elasticsearch helpers API."""
from elasticsearch import helpers


def bulk_index(client, index: str, docs: list[dict]) -> int:
    """Bulk-index ``docs`` into ``index``; return the number indexed."""
    actions = ({"_index": index, "_source": d} for d in docs)
    ok, _ = helpers.bulk(client, actions)
    return ok
