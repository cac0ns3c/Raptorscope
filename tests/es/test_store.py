# SPDX-License-Identifier: GPL-3.0-or-later
import os

import pytest

from raptorscope.api.store import Store
from raptorscope.es.store import ESStore


def test_esstore_satisfies_store_protocol():
    # runtime_checkable structural check — no live ES needed
    assert isinstance(ESStore.__new__(ESStore), Store)


@pytest.mark.skipif(
    not os.environ.get("RAPTORSCOPE_ES_URL"),
    reason="no live Elasticsearch (set RAPTORSCOPE_ES_URL to run)",
)
def test_esstore_roundtrip_live():
    from elasticsearch import Elasticsearch

    store = ESStore(Elasticsearch(os.environ["RAPTORSCOPE_ES_URL"]))
    assert isinstance(store.hosts(), list)
