# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared ECS document helpers."""


def ecs_base(
    host: dict,
    dataset: str,
    category: list[str] | None = None,
    type_: list[str] | None = None,
) -> dict:
    """Return the common ECS event/host skeleton shared by every normalizer.

    ``category``/``type_`` default to the persistence-style
    ``["configuration"]``/``["info"]`` but may be overridden per artifact.
    """
    return {
        "event": {
            "kind": "event",
            "module": "raptorscope",
            "dataset": dataset,
            "category": category or ["configuration"],
            "type": type_ or ["info"],
        },
        "host": host,
    }


def code_signature(raw) -> dict | None:
    """Map a Velociraptor ``CodeSignature`` object to ECS ``code_signature``.

    Returns ``None`` when the input is absent/unusable so callers can omit the
    field entirely rather than emit an empty object.
    """
    if not isinstance(raw, dict):
        return None
    sig: dict = {}
    if "Exists" in raw:
        sig["exists"] = bool(raw.get("Exists"))
    if raw.get("SubjectName") is not None:
        sig["subject_name"] = raw.get("SubjectName")
    if "Trusted" in raw:
        sig["trusted"] = bool(raw.get("Trusted"))
    return sig or None
