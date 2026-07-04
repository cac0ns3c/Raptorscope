# SPDX-License-Identifier: GPL-3.0-or-later
"""Integration: the ES-native detector agrees with the in-process evaluator.

Skipped unless a live Elasticsearch with the sample data is reachable at
RAPTORSCOPE_TEST_ES (default http://localhost:9200). This guards the field-type
parity contract (process.command_line must be `wildcard`, not analyzed `text`).
"""
import os

import pytest

ES_URL = os.environ.get("RAPTORSCOPE_TEST_ES", "http://localhost:9200")
HOST = os.environ.get("RAPTORSCOPE_TEST_HOST", "mac-victim")


def _es():
    try:
        from elasticsearch import Elasticsearch
    except ImportError:
        pytest.skip("elasticsearch client not installed")
    es = Elasticsearch(ES_URL)
    try:
        if not es.ping() or es.count(index="raptorscope-*")["count"] == 0:
            pytest.skip("no live raptorscope data")
    except Exception:
        pytest.skip("Elasticsearch not reachable")
    return es


def test_es_native_matches_in_process():
    es = _es()
    from raptorscope.detect.es_detector import ESDetector
    from raptorscope.detect.evaluate import load_rules, run_rules
    from raptorscope.es.store import ESStore

    docs = ESStore(es).search(host=HOST, size=10000)
    in_proc = {
        (a["rule_id"], a["doc_id"])
        for a in run_rules(docs, load_rules("detections/sigma"))
    }
    es_native = {
        (a["rule_id"], a["doc_id"]) for a in ESDetector(es).run(host=HOST)
    }
    assert es_native == in_proc, (
        f"in-proc only: {in_proc - es_native}, es only: {es_native - in_proc}"
    )
