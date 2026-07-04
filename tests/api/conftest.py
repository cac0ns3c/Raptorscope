# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared seed for API contract tests — an InMemoryStore built from the Phase-2
fixtures via the real normalizers, for two hosts (one dirty, one benign)."""
import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from raptorscope.api.app import create_app
from raptorscope.api.store import InMemoryStore
from raptorscope.normalize.btm import normalize_btm
from raptorscope.normalize.config_profiles import normalize_config_profiles
from raptorscope.normalize.cron import normalize_cron
from raptorscope.normalize.inventory import normalize_inventory
from raptorscope.normalize.launch_items import normalize_launch_items
from raptorscope.normalize.login_items import normalize_login_items
from raptorscope.normalize.processes import normalize_processes
from raptorscope.normalize.quarantine import normalize_quarantine
from raptorscope.normalize.tcc import normalize_tcc

FIX = pathlib.Path("fixtures/velociraptor")
DIRTY_HOST = "mac-victim"
CLEAN_HOST = "mac-clean"


def _rows(name):
    return json.loads((FIX / name).read_text())


def seed_docs():
    dirty = {"name": DIRTY_HOST, "os": {"type": "macos"}}
    clean = {"name": CLEAN_HOST, "os": {"type": "macos"}}
    docs = []
    docs += normalize_launch_items(_rows("launch_items.raw.json"), dirty)
    docs += normalize_login_items(_rows("login_items.raw.json"), dirty)
    docs += normalize_cron(_rows("cron_items.raw.json"), dirty)
    docs += normalize_config_profiles(_rows("config_profiles.raw.json"), dirty)
    docs += normalize_btm(_rows("btm_items.raw.json"), dirty)
    docs += normalize_processes(_rows("processes.raw.json"), dirty)
    docs += normalize_quarantine(_rows("quarantine.raw.json"), dirty)
    docs += normalize_tcc(_rows("tcc.raw.json"), dirty)
    docs += normalize_inventory(_rows("installed_apps.raw.json"), dirty)
    # Clean host: only the benign leading rows of two artifacts — no rule fires.
    docs += normalize_launch_items(_rows("launch_items.raw.json")[:2], clean)
    docs += normalize_processes(_rows("processes.raw.json")[:2], clean)
    return docs


DIRTY_DOC_COUNT = 22
CLEAN_DOC_COUNT = 4


@pytest.fixture
def store():
    return InMemoryStore(seed_docs())


@pytest.fixture
def client(store):
    return TestClient(create_app(store))
