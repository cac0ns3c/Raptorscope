# SPDX-License-Identifier: GPL-3.0-or-later
"""Pairing guard: every dataset has a rule; no rule selects a dead field."""
import glob

import yaml

# Fields the normalizers are known to emit (extend as datasets are added).
EMITTED_FIELDS = {
    "event.dataset",
    "file.path",
    "file.name",
    "process.executable",
    "process.command_line",
    "process.code_signature.exists",
    "process.code_signature.subject_name",
    "process.code_signature.trusted",
    "raptorscope.persistence.type",
    "raptorscope.persistence.label",
    "raptorscope.persistence.run_at_load",
}


def _rule_datasets_and_fields(doc):
    det = doc.get("detection", {})
    datasets, fields = set(), set()
    for key, sel in det.items():
        if not isinstance(sel, dict):
            continue
        for field, val in sel.items():
            base = field.split("|")[0]
            fields.add(base)
            if base == "event.dataset":
                datasets.update(v for v in ([val] if isinstance(val, str) else val))
    return datasets, fields


def check_pairing(datasets: set, rules_dir: str) -> list:
    """Return a list of pairing problems (empty list = OK)."""
    problems, covered = [], set()
    for path in glob.glob(f"{rules_dir}/*.yml"):
        with open(path) as fh:
            doc = yaml.safe_load(fh)
        ds, fields = _rule_datasets_and_fields(doc)
        covered |= ds
        dead = {f for f in fields if f not in EMITTED_FIELDS}
        if dead:
            problems.append(f"{path}: selects unknown fields {sorted(dead)}")
    for d in datasets - covered:
        problems.append(f"dataset '{d}' has no paired Sigma rule")
    return problems
