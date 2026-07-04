# SPDX-License-Identifier: GPL-3.0-or-later
"""Every v1 dataset must ship with at least one paired Sigma rule."""
from raptorscope.detect.pairing import ALL_DATASETS, check_pairing


def test_all_datasets_are_paired_and_no_dead_fields():
    problems = check_pairing(ALL_DATASETS, "detections/sigma")
    assert problems == [], problems
