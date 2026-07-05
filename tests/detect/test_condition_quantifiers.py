# SPDX-License-Identifier: GPL-3.0-or-later
"""Sigma quantifier conditions (all of / N of / prefix) match pysigma/ES
semantics, so the in-process evaluator stays parity-correct if a rule adopts them."""
from raptorscope.detect.evaluate import _eval_condition as ev


def test_all_of_them():
    assert ev("all of them", {"a": True, "b": True})
    assert not ev("all of them", {"a": True, "b": False})


def test_n_of_them_requires_at_least_n():
    r = {"a": True, "b": True, "c": False}
    assert ev("2 of them", r)          # 2 true >= 2
    assert not ev("3 of them", r)      # only 2 true, need 3  (old heuristic said any->True)
    assert ev("1 of them", r)
    assert not ev("1 of them", {"a": False, "b": False})


def test_prefix_scoped_quantifier():
    r = {"selection_a": True, "selection_b": False, "filter_x": True}
    # "1 of selection_*" scopes to selection_* only (filter_x ignored)
    assert ev("1 of selection_*", r)
    assert not ev("2 of selection_*", r)   # only selection_a true within scope
    # "all of selection*" must NOT be satisfied by the unrelated filter block
    assert not ev("all of selection*", r)
    assert ev("all of selection*", {"selection_a": True, "selection_b": True, "filter_x": False})
