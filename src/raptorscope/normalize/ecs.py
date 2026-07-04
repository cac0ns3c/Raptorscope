# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared ECS document helpers."""


def ecs_base(host: dict, dataset: str) -> dict:
    """Return the common ECS event/host skeleton shared by every normalizer."""
    return {
        "event": {
            "kind": "event",
            "module": "raptorscope",
            "dataset": dataset,
            "category": ["configuration"],
            "type": ["info"],
        },
        "host": host,
    }
