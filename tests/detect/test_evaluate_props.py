# SPDX-License-Identifier: GPL-3.0-or-later
"""Property/robustness tests for the Sigma condition parser and field matchers.

Exhaustive over small boolean domains (no external property-testing dep) plus
fuzz-style checks that malformed input never raises.
"""
import itertools

import pytest

from raptorscope.detect.evaluate import (
    _eval_condition,
    _field_matches,
    _one_matches,
)


@pytest.mark.parametrize("a,b,c", list(itertools.product([True, False], repeat=3)))
def test_boolean_algebra_matches_python(a, b, c):
    r = {"sa": a, "sb": b, "sc": c}
    assert _eval_condition("sa and sb", r) == (a and b)
    assert _eval_condition("sa or sb", r) == (a or b)
    assert _eval_condition("not sa", r) == (not a)
    assert _eval_condition("sa and not sb", r) == (a and not b)
    assert _eval_condition("(sa or sb) and not sc", r) == ((a or b) and not c)
    assert _eval_condition("sa or sb and sc", r) == (a or (b and c))  # and binds tighter


@pytest.mark.parametrize("vals", list(itertools.product([True, False], repeat=3)))
def test_quantifiers(vals):
    r = {"s1": vals[0], "s2": vals[1], "s3": vals[2]}
    assert _eval_condition("all of them", r) == all(vals)
    assert _eval_condition("1 of them", r) == any(vals)
    assert _eval_condition("any of them", r) == any(vals)


@pytest.mark.parametrize(
    "cond",
    ["", "   ", "(", ")", "sa and", "and sa", "((sa)", "sa or or sb", "unknown_sel",
     "not not sa", "()"],
)
def test_malformed_conditions_never_raise(cond):
    out = _eval_condition(cond, {"sa": True, "sb": False})
    assert isinstance(out, bool)


def test_double_negation_and_unknown_token():
    assert _eval_condition("not not sa", {"sa": True}) is True
    # an unreferenced selection name evaluates to False, not an error
    assert _eval_condition("ghost", {"sa": True}) is False


@pytest.mark.parametrize(
    "mods,value,expected,want",
    [
        (["contains"], "/private/tmp/x", "tmp", True),
        (["contains"], None, "tmp", False),          # None-safe
        (["startswith"], "/usr/bin/x", "/usr", True),
        (["endswith"], "beacon.sh", ".sh", True),
        (["startswith"], None, "/usr", False),
        ([], 5099, 5099, True),                       # non-string eq
        ([], "5099", 5099, False),                    # eq is type-strict
    ],
)
def test_one_matches(mods, value, expected, want):
    assert _one_matches(value, expected, mods) is want


def test_field_matches_list_is_or():
    doc = {"process": {"name": "helper"}}
    assert _field_matches(doc, "process.name", ["launchd", "helper"]) is True
    assert _field_matches(doc, "process.name", ["launchd", "safari"]) is False
    # missing field never raises
    assert _field_matches(doc, "does.not.exist", "x") is False
