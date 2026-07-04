# SPDX-License-Identifier: GPL-3.0-or-later
"""AI features for macOS DFIR triage, built on the ``AIClient`` seam.

Each function is pure over its inputs (already fetched from the store by the API
layer) so it can be unit-tested with a fake client.
"""
import json
from typing import Callable

from .client import AIClient

_PERSONA = (
    "You are a senior macOS DFIR analyst assisting with first-hour incident "
    "triage. You reason from the evidence provided, are precise about what is and "
    "isn't suspicious, cite the concrete fields that drive your conclusion, and "
    "never invent artifacts that aren't in the data."
)


def triage_alert(ai: AIClient, alert: dict, doc: dict) -> dict:
    """Explain why an alert fired and what to do next."""
    prompt = (
        "A detection fired on a macOS host. Assess it.\n\n"
        f"Rule: {alert.get('title')}\n"
        f"Severity: {alert.get('level')}\n"
        f"Dataset: {alert.get('dataset')}\n"
        f"Matched fields: {json.dumps(alert.get('evidence', {}), indent=2)}\n\n"
        f"Full evidence document:\n{json.dumps(doc, indent=2)}\n\n"
        "Respond in four short sections with these exact headers:\n"
        "**Why it fired** — the behavior in plain English.\n"
        "**MITRE** — the technique(s) and why they apply.\n"
        "**Assessment** — likely malicious vs benign, with the signal that decides it.\n"
        "**Next steps** — 2-4 concrete triage actions."
    )
    return {"analysis": ai.text(_PERSONA, prompt, max_tokens=1400)}


def summarize_case(ai: AIClient, overview: dict, alerts: list[dict]) -> dict:
    """Produce a first-hour incident narrative for the case."""
    top = alerts[:20]
    prompt = (
        "Write a first-hour triage brief for this macOS host.\n\n"
        f"Case: {overview.get('case')}\n"
        f"Document counts by dataset: {json.dumps(overview.get('datasets', {}))}\n"
        f"Persistence by type: {json.dumps(overview.get('persistence_types', {}))}\n"
        f"Unsigned: {json.dumps(overview.get('unsigned', {}))}\n"
        f"Fired detections ({len(alerts)} total, showing {len(top)}):\n"
        f"{json.dumps(top, indent=2)}\n\n"
        "Write 2-4 tight paragraphs: what stands out, the most likely storyline "
        "tying the alerts together, and a prioritized recommendation. Lead with the "
        "bottom line. Be concrete about hosts, paths, and techniques; don't hedge."
    )
    return {"summary": ai.text(_PERSONA, prompt, max_tokens=1600)}


_QUERY_SCHEMA = {
    "type": "object",
    "properties": {
        "q": {"type": "string", "description": "free-text term, or empty"},
        "dataset": {"type": "string", "description": "one dataset or empty for all"},
        "field": {"type": "string", "description": "ECS field path or empty"},
        "op": {"type": "string", "enum": ["contains", "eq", "startswith", "endswith"]},
        "value": {"type": "string", "description": "field filter value or empty"},
    },
    "required": ["q", "dataset", "field", "op", "value"],
    "additionalProperties": False,
}


def compile_query(ai: AIClient, question: str, datasets: list[str]) -> dict:
    """Translate a natural-language question into search parameters."""
    prompt = (
        "Translate the analyst's question into a search over normalized macOS "
        "DFIR events. Use free-text `q` for keywords/paths, `dataset` to scope to "
        "one artifact type, and an optional `field`/`op`/`value` for a precise "
        "filter. Leave fields empty when not needed.\n\n"
        f"Available datasets: {datasets}\n"
        "Common fields: file.path, process.executable, process.command_line, "
        "process.name, raptorscope.persistence.type, raptorscope.tcc.service, "
        "raptorscope.tcc.allowed, raptorscope.app.signed, url.full, host.name.\n\n"
        f'Question: "{question}"'
    )
    raw = ai.json(_PERSONA, prompt, _QUERY_SCHEMA, max_tokens=400)
    # Drop empty fields; keep only known keys.
    out = {k: v for k, v in raw.items() if k in _QUERY_SCHEMA["properties"] and v}
    if not out.get("field"):
        out.pop("op", None)
        out.pop("value", None)
    return {"query": out}


_COPILOT_TOOLS = [
    {
        "name": "search_case",
        "description": "Search the case's normalized events. Free-text `q`, optional "
        "`dataset` scope, optional `field`/`op`/`value` filter.",
        "input_schema": {
            "type": "object",
            "properties": {
                "q": {"type": "string"},
                "dataset": {"type": "string"},
                "field": {"type": "string"},
                "op": {"type": "string"},
                "value": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": [],
        },
    },
    {
        "name": "list_alerts",
        "description": "List the detections that fired for this case.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_overview",
        "description": "Get per-dataset counts and signing-integrity tallies.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

_COPILOT_SYSTEM = _PERSONA + (
    " You are running as an investigation copilot. Use the provided tools to gather "
    "evidence from the case before answering — search for suspicious artifacts, list "
    "the fired detections, check the overview. Then give a triage verdict: a clear "
    "bottom-line judgment, the supporting evidence (cite the specific paths, "
    "processes, or services you found), and recommended next steps. Ground every "
    "claim in a tool result; do not speculate beyond the data."
)


def run_copilot(
    ai: AIClient, question: str, dispatch: Callable[[str, dict], object]
) -> dict:
    """Agentic loop: the model queries the case via tools, then returns a verdict."""
    result = ai.agentic(
        _COPILOT_SYSTEM,
        f"Investigate and answer: {question}",
        _COPILOT_TOOLS,
        dispatch,
        max_tokens=2600,
        max_iters=6,
    )
    return {"answer": result.get("answer", ""), "citations": result.get("citations", [])}
