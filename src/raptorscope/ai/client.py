# SPDX-License-Identifier: GPL-3.0-or-later
"""LLM seam for the AI features.

``AIClient`` is the interface the AI service depends on; ``AnthropicAI`` is the
production implementation over the Claude API (Anthropic SDK). Tests inject a
fake implementing the same three primitives, so the whole AI surface is testable
with no network and no API key.
"""
import json
import os
from typing import Callable, Iterator, Protocol, runtime_checkable

MODEL = "claude-opus-4-8"


@runtime_checkable
class AIClient(Protocol):
    def text(self, system: str, user: str, max_tokens: int = 1024) -> str: ...

    def stream_text(
        self, system: str, user: str, max_tokens: int = 1024
    ) -> Iterator[str]: ...

    def json(
        self, system: str, user: str, schema: dict, max_tokens: int = 1024
    ) -> dict: ...

    def agentic(
        self,
        system: str,
        user: str,
        tools: list[dict],
        dispatch: Callable[[str, dict], object],
        max_tokens: int = 2048,
        max_iters: int = 6,
    ) -> dict: ...


class AnthropicAI:
    """Claude-backed ``AIClient``. Uses ``claude-opus-4-8`` by default."""

    def __init__(self, client, model: str = MODEL):
        self._client = client
        self.model = model

    def _blocks_text(self, content) -> str:
        return "".join(b.text for b in content if getattr(b, "type", "") == "text")

    def text(self, system: str, user: str, max_tokens: int = 1024) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return self._blocks_text(resp.content)

    def stream_text(
        self, system: str, user: str, max_tokens: int = 1024
    ) -> Iterator[str]:
        with self._client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            yield from stream.text_stream

    def json(
        self, system: str, user: str, schema: dict, max_tokens: int = 1024
    ) -> dict:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        return json.loads(self._blocks_text(resp.content))

    def agentic(
        self,
        system: str,
        user: str,
        tools: list[dict],
        dispatch: Callable[[str, dict], object],
        max_tokens: int = 2048,
        max_iters: int = 6,
    ) -> dict:
        messages = [{"role": "user", "content": user}]
        calls: list[dict] = []
        for _ in range(max_iters):
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system,
                tools=tools,
                messages=messages,
            )
            if resp.stop_reason != "tool_use":
                return {"answer": self._blocks_text(resp.content), "citations": calls}
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for b in resp.content:
                if getattr(b, "type", "") == "tool_use":
                    out = dispatch(b.name, dict(b.input))
                    calls.append({"tool": b.name, "input": dict(b.input)})
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": b.id,
                            "content": json.dumps(out)[:20000],
                        }
                    )
            messages.append({"role": "user", "content": results})
        # ran out of iterations — return whatever we have
        return {"answer": "(analysis truncated — iteration limit reached)", "citations": calls}


def build_ai_from_env() -> AIClient | None:
    """Return an ``AnthropicAI`` if an API key is configured, else ``None``.

    AI features are opt-in and fully configurable via env — point the client at
    any Anthropic-API-compatible endpoint (a gateway/proxy such as LiteLLM,
    Cloudflare AI Gateway, or a self-hosted router), pick any model, and supply
    the key:

    - ``RAPTORSCOPE_AI_KEY`` (or ``ANTHROPIC_API_KEY``) — required; enables AI.
    - ``RAPTORSCOPE_AI_MODEL`` (or ``ANTHROPIC_MODEL``) — model id (default
      ``claude-opus-4-8``).
    - ``RAPTORSCOPE_AI_BASE_URL`` (or ``ANTHROPIC_BASE_URL``) — endpoint override.

    With no key the endpoints report ``enabled: false`` and return 503.
    """
    key = os.environ.get("RAPTORSCOPE_AI_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        import anthropic
    except ImportError:
        return None
    model = (
        os.environ.get("RAPTORSCOPE_AI_MODEL")
        or os.environ.get("ANTHROPIC_MODEL")
        or MODEL
    )
    base_url = os.environ.get("RAPTORSCOPE_AI_BASE_URL") or os.environ.get(
        "ANTHROPIC_BASE_URL"
    )
    kwargs: dict = {"api_key": key}
    if base_url:
        kwargs["base_url"] = base_url
    return AnthropicAI(anthropic.Anthropic(**kwargs), model=model)
