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
    "process.name",
    "process.pid",
    "process.parent.pid",
    "user.name",
    "url.full",
    "url.original",
    "raptorscope.quarantine.sender",
    "raptorscope.tcc.service",
    "raptorscope.tcc.client",
    "raptorscope.tcc.client_type",
    "raptorscope.tcc.allowed",
    "process.code_signature.exists",
    "process.code_signature.subject_name",
    "process.code_signature.trusted",
    "raptorscope.persistence.type",
    "raptorscope.persistence.label",
    "raptorscope.persistence.run_at_load",
    "raptorscope.persistence.hidden",
    "raptorscope.persistence.schedule",
    "raptorscope.persistence.payload_type",
    "raptorscope.persistence.signed",
    "raptorscope.persistence.btm_type",
    "raptorscope.persistence.developer",
    "raptorscope.persistence.uuid",
    "raptorscope.app.name",
    "raptorscope.app.bundle_id",
    "raptorscope.app.version",
    "raptorscope.app.signed",
    # macos.network
    "source.ip",
    "source.port",
    "destination.ip",
    "destination.address",
    "destination.port",
    "network.transport",
    "network.type",
    "network.direction",
    "raptorscope.network.state",
    # macos.unifiedlog (raw Unified Log evidence); reuses raptorscope.tcc.* above
    "event.action",
    "raptorscope.unifiedlog.subsystem",
    "raptorscope.unifiedlog.category",
    "raptorscope.unifiedlog.process",
    "raptorscope.unifiedlog.pid",
    "raptorscope.unifiedlog.msg_id",
    "raptorscope.unifiedlog.right",
    "raptorscope.unifiedlog.granted",
}


# Datasets produced from a Velociraptor collection (the mac-victim sample
# exercises all of these).
COLLECTION_DATASETS = {
    "macos.persistence",
    "macos.process",
    "macos.quarantine",
    "macos.tcc",
    "macos.inventory",
    "macos.network",
}
# Raw-evidence datasets parsed directly off disk (no Velociraptor).
EVIDENCE_DATASETS = {
    "macos.unifiedlog",
}
# Every ECS dataset the normalizers emit; the pairing guard requires each to
# have at least one Sigma rule.
ALL_DATASETS = COLLECTION_DATASETS | EVIDENCE_DATASETS


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
