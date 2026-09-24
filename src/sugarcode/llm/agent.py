"""SugarCode copilot: a question in, module-backed answers out.

The trained router picks the most relevant modules, their tools are offered
to the chat model (OpenAI function calling), tool calls run the real SugarCode
functions, and the model writes the answer from the tool results. Profiles are
tried in route order; the first that answers wins. With no model reachable,
the result still lists the routed modules and tools so the user can run them.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

from .providers import ChatClient, ProviderError, resolve, resolve_route
from .router import route as route_modules
from .tools import call_tool, tools_for_modules

SYSTEM = (
    "You are SugarCode, a computational-biology copilot. Use the provided tools, which run real "
    "SugarCode modules, whenever they can compute the answer; do not invent numbers. After tool "
    "results arrive, answer briefly and specifically, name the module behind each number, and say "
    "plainly when a tool errored or cannot answer."
)


@dataclass
class AskResult:
    answer: str | None
    profile: str | None
    modules: list[dict]
    tools: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return {"answer": self.answer, "profile": self.profile, "modules": self.modules,
                "tools_offered": self.tools, "tool_calls": self.tool_calls,
                "skipped_profiles": self.skipped, "error": self.error}


def _run(client: ChatClient, question: str, tools, max_steps: int) -> tuple[str, list[dict]]:
    schemas = [t.openai_schema() for t in tools] if client.supports_tools else None
    messages: list[dict] = [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": question}]
    if not client.supports_tools:
        listing = "\n".join(f"- {t.name}: {t.description}" for t in tools)
        messages[1]["content"] += ("\n\nRelevant SugarCode tools (you cannot call them; say which to "
                                   f"run and with what inputs):\n{listing}")
    trace: list[dict] = []
    for _ in range(max_steps):
        msg = client.chat(messages, tools=schemas)
        calls = msg.get("tool_calls") or []
        if not calls:
            return (msg.get("content") or "").strip(), trace
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": calls})
        for c in calls:
            fn = c.get("function", {})
            result = call_tool(fn.get("name", ""), fn.get("arguments") or "{}")
            trace.append({"tool": fn.get("name"), "arguments": fn.get("arguments"),
                          "ok": "error" not in result})
            messages.append({"role": "tool", "tool_call_id": c.get("id", ""),
                             "content": json.dumps(result)[:12000]})
    messages.append({"role": "user", "content": "Answer now from the tool results so far."})
    return (client.chat(messages).get("content") or "").strip(), trace


def ask(question: str, profile: str | None = None, route: str | None = None,
        model: str | None = None, allow_paid: bool | None = None, k_modules: int = 3,
        max_tools: int = 24, max_steps: int = 4, env: dict | None = None) -> AskResult:
    """Answer with module tools. `profile` pins one profile; otherwise the route is tried in order."""
    mods = route_modules(question, k=k_modules)
    tools = tools_for_modules([m["module"] for m in mods], limit=max_tools)
    names = [t.name for t in tools]
    if profile:
        try:
            clients, skipped = [resolve(profile, model=model, env=env, allow_paid=allow_paid)], []
        except ProviderError as e:
            return AskResult(None, None, mods, names, skipped=[str(e)], error=str(e))
    else:
        clients, skipped = resolve_route(env=env, route=route, allow_paid=allow_paid)
    errors = list(skipped)
    for c in clients:
        try:
            answer, trace = _run(c, question, tools, max_steps)
            return AskResult(answer, c.profile, mods, names, trace, errors)
        except ProviderError as e:
            errors.append(str(e))
    return AskResult(None, None, mods, names, skipped=errors,
                     error="no model profile answered; the routed modules and tools are listed so you can run them directly")
