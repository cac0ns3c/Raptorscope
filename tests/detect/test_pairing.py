# SPDX-License-Identifier: GPL-3.0-or-later
from raptorscope.detect.pairing import check_pairing


def test_persistence_dataset_is_paired():
    problems = check_pairing({"macos.persistence"}, "detections/sigma")
    assert problems == []
