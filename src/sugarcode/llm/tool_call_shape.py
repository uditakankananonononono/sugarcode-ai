"""Shape checks for model-supplied tool calls (H02). AUTHORED, NOT RUN.

One helper for both consumers: agent._run (OpenAI style: {"id", "function": {"name", "arguments"}})
and shared.shared_ask (flat style from instinct_models: {"name", "arguments"}, flat=True).

Rules (peer policy relayed by Main): entry is a dict; for OpenAI style `function` is present and a dict;
name is a str (empty str is allowed here and is then an unknown tool); id is a str or missing.
`arguments` is NOT judged here; call_tool validates it. A missing/None/falsey tool_calls container means no calls;
a truthy non-list container raises. Nothing here normalizes or skips malformed data.
"""
from __future__ import annotations

from dataclasses import dataclass

from .providers import ProviderError

__all__ = ["ToolCallShapeError", "ToolCallFields", "tool_call_container", "tool_call_fields", "tool_call_batch"]


class ToolCallShapeError(ProviderError):
    """The model/provider returned a tool call (or tool_calls container) of the wrong shape."""


@dataclass(frozen=True)
class ToolCallFields:
    name: str
    arguments: object
    id: str


def tool_call_container(raw) -> list:
    """[] for missing/falsey; the list itself for a list; ToolCallShapeError for any truthy non-list."""
    if not raw:
        return []
    if not isinstance(raw, list):
        raise ToolCallShapeError(f"tool_calls must be a list, got {type(raw).__name__}")
    return raw


def tool_call_fields(call, *, flat: bool = False, index: int | None = None) -> ToolCallFields:
    where = "tool call" if index is None else f"tool call {index}"
    if not isinstance(call, dict):
        raise ToolCallShapeError(f"{where} must be an object, got {type(call).__name__}")
    if flat:
        body = call
    else:
        body = call.get("function")
        if not isinstance(body, dict):
            raise ToolCallShapeError(f"{where} function must be an object, got {type(body).__name__}")
    name = body.get("name")
    if not isinstance(name, str):
        raise ToolCallShapeError(f"{where} name must be a string, got {type(name).__name__}")
    ident = call.get("id", "")
    if not isinstance(ident, str):
        raise ToolCallShapeError(f"{where} id must be a string when present, got {type(ident).__name__}")
    return ToolCallFields(name=name, arguments=body.get("arguments"), id=ident)


def tool_call_batch(raw) -> list[ToolCallFields]:
    """Validate the container and EVERY entry (OpenAI style) before returning; raises on the first bad one."""
    return [tool_call_fields(c, index=i) for i, c in enumerate(tool_call_container(raw))]
