# SPDX-License-Identifier: GPL-3.0-or-later
"""In-process evaluation of Sigma rules against ECS docs (query-on-read).

The Sigma YAMLs under ``detections/`` remain the detection source of truth; this
module evaluates them directly so the API can surface alerts without a live
Elasticsearch. It supports exactly the Sigma surface the raptorscope rules use:
map selections with ``contains``/``startswith``/``endswith`` modifiers, list
values as OR, multiple fields as AND, and a boolean ``condition`` over named
selection blocks (``and``/``or``/``not``/parens, plus ``all of``/``N of them``).
"""
import glob
from dataclasses import dataclass

import yaml


@dataclass
class Rule:
    id: str
    title: str
    level: str
    tags: list
    datasets: set
    detection: dict


def _dig(doc, path):
    cur = doc
    for key in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _field_matches(doc, field_spec, expected) -> bool:
    base, *mods = field_spec.split("|")
    value = _dig(doc, base)
    candidates = expected if isinstance(expected, list) else [expected]
    return any(_one_matches(value, m, mods) for m in candidates)


def _one_matches(value, expected, mods) -> bool:
    if "contains" in mods:
        return value is not None and str(expected) in str(value)
    if "startswith" in mods:
        return value is not None and str(value).startswith(str(expected))
    if "endswith" in mods:
        return value is not None and str(value).endswith(str(expected))
    return value == expected


def _map_matches(doc, mapping: dict) -> bool:
    return all(_field_matches(doc, f, v) for f, v in mapping.items())


def _block_matches(doc, block) -> bool:
    if isinstance(block, list):  # list of maps = OR
        return any(_map_matches(doc, m) for m in block)
    if isinstance(block, dict):
        return _map_matches(doc, block)
    return False


def _eval_of(low: str, results: dict) -> bool:
    """Sigma quantifier: ``all of them`` / ``N of them`` / ``N of <prefix>*``.

    Scope is all blocks (``them``) or those whose name matches the prefix pattern;
    ``all`` requires every scoped block true, ``N``/``any`` at least N. Matches
    pysigma/ES semantics so the two detection engines agree.
    """
    qty, _, pattern = low.partition(" of ")
    qty, pattern = qty.strip(), pattern.strip()
    if pattern in ("them", "these", "") or pattern == "all":
        names = list(results)
    else:
        pat = pattern.rstrip("*")
        names = [n for n in results if n.lower().startswith(pat)]
    truthy = sum(1 for n in names if results.get(n))
    if qty == "all":
        return bool(names) and truthy == len(names)
    if qty in ("any", "1"):
        return truthy >= 1
    try:
        return truthy >= int(qty)
    except ValueError:
        return truthy >= 1


def _eval_condition(cond: str, results: dict) -> bool:
    cond = (cond or "").strip()
    low = cond.lower()
    if " of " in f" {low} ":  # "all of them" / "2 of them" / "1 of selection*"
        return _eval_of(low, results)
    tokens = cond.replace("(", " ( ").replace(")", " ) ").split()
    if not tokens:
        return all(results.values()) if results else True

    pos = 0

    def parse_or():
        nonlocal pos
        v = parse_and()
        while pos < len(tokens) and tokens[pos] == "or":
            pos += 1
            v = parse_and() or v
        return v

    def parse_and():
        nonlocal pos
        v = parse_not()
        while pos < len(tokens) and tokens[pos] == "and":
            pos += 1
            v = parse_not() and v
        return v

    def parse_not():
        nonlocal pos
        if pos < len(tokens) and tokens[pos] == "not":
            pos += 1
            return not parse_not()
        return parse_atom()

    def parse_atom():
        nonlocal pos
        if pos >= len(tokens):  # malformed condition (dangling operator/paren)
            return False
        tok = tokens[pos]
        pos += 1
        if tok == "(":
            v = parse_or()
            if pos < len(tokens) and tokens[pos] == ")":
                pos += 1
            return v
        return bool(results.get(tok, False))

    return parse_or()


def rule_matches(doc, detection: dict) -> bool:
    blocks = {k: v for k, v in detection.items() if k != "condition"}
    results = {name: _block_matches(doc, sel) for name, sel in blocks.items()}
    return _eval_condition(detection.get("condition", ""), results)


def _rule_datasets(detection: dict) -> set:
    datasets = set()
    for name, sel in detection.items():
        if name == "condition" or not isinstance(sel, dict):
            continue
        val = sel.get("event.dataset")
        if isinstance(val, str):
            datasets.add(val)
        elif isinstance(val, list):
            datasets.update(v for v in val if isinstance(v, str))
    return datasets


def load_rules(rules_dir: str) -> list[Rule]:
    rules = []
    for path in sorted(glob.glob(f"{rules_dir}/*.yml")):
        with open(path) as fh:
            doc = yaml.safe_load(fh)
        detection = doc.get("detection", {})
        rules.append(
            Rule(
                id=doc.get("id"),
                title=doc.get("title"),
                level=doc.get("level", "informational"),
                tags=doc.get("tags", []),
                datasets=_rule_datasets(detection),
                detection=detection,
            )
        )
    return rules


def _evidence(doc, detection: dict) -> dict:
    """Every field the rule selects on (across all blocks) → its doc value.

    This is the honest "why it fired" context; the caller pairs it with
    ``doc_id`` so the UI can pivot to the full evidence document.
    """
    fields = {}
    for name, block in detection.items():
        if name == "condition":
            continue
        maps = block if isinstance(block, list) else [block]
        for mapping in maps:
            if not isinstance(mapping, dict):
                continue
            for field_spec in mapping:
                base = field_spec.split("|")[0]
                fields[base] = _dig(doc, base)
    return fields


def run_rules(docs, rules) -> list[dict]:
    """Return one alert per (rule, matching doc)."""
    alerts = []
    for doc in docs:
        dataset = _dig(doc, "event.dataset")
        for rule in rules:
            if rule.datasets and dataset not in rule.datasets:
                continue
            if rule_matches(doc, rule.detection):
                alerts.append(
                    {
                        "rule_id": rule.id,
                        "title": rule.title,
                        "level": rule.level,
                        "dataset": dataset,
                        "doc_id": doc.get("_id"),
                        "evidence": _evidence(doc, rule.detection),
                    }
                )
    return alerts
