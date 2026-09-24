"""SugarCode on the shared model layer (instinct_models, vendored from shared-models).

- `shared_config()`   ProductConfig for product "sugarcode" from INSTINCT_* env.
- `shared_ask()`      trained module router picks SugarCode tools -> shared Needle-first
                      Router (Needle -> Ornith local -> Inkling local -> Inkling HF router)
                      -> the chosen tool call is executed against the real module.
                      private=True never reaches the hosted route.
- `SugarcodeDataset`  DomainDataset for the shared Needle LoRA pipeline, built from
                      SugarCode's own verified-executable tool calls plus off-topic rows.
No paid route is reachable from here; Fugu stays in sugarcode.llm.providers behind
SUGARCODE_ALLOW_PAID.
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Iterable

from instinct_models import ProductConfig, Router, Task, load_config
from instinct_models.training.dataset import ExampleRow, build_needle_jsonl

from .router import route as route_modules
from .tools import call_tool, tools_for_modules

PRODUCT = "sugarcode"

OFF_TOPIC = [
    "hi", "thanks, that's all", "what can you do?", "tell me a joke", "who made you?",
    "what's the weather like today?", "summarise our chat so far", "good morning",
    "can you explain what a gene is in simple words?", "how do I cite SugarCode in a paper?",
    "what time is it in London?", "write a haiku about cells", "ok", "never mind",
    "which of these options would you pick?", "explain that again more slowly",
]


def shared_config(env: dict | None = None, path: str | None = None) -> ProductConfig:
    e = dict(os.environ if env is None else env)
    e.setdefault("INSTINCT_PRODUCT", PRODUCT)
    cfg = load_config(e, path)
    if cfg.product != PRODUCT:
        raise ValueError(f"INSTINCT_PRODUCT is {cfg.product!r}; SugarCode must run as {PRODUCT!r}")
    return cfg


def shared_tools(question: str, k: int = 3, limit: int = 12) -> tuple[list[dict], list[dict]]:
    """Router-picked SugarCode tools as the plain function dicts instinct_models expects."""
    mods = route_modules(question, k=k)
    tools = tools_for_modules([m["module"] for m in mods], limit=limit)
    return [t.openai_schema()["function"] for t in tools], mods


def shared_ask(question: str, *, private: bool = False, execute: bool = True, router: Router | None = None,
               env: dict | None = None, k: int = 3) -> dict:
    tools, mods = shared_tools(question, k=k)
    router = router or Router.from_config(shared_config(env))
    messages = [{"role": "system", "content": "You are SugarCode's copilot. Call one of the given tools when it answers the request."},
                {"role": "user", "content": question}]
    res = router.run(Task(messages=messages, tools=tools, private=private))
    out = {"modules": mods, "tools_offered": [t["name"] for t in tools],
           "attempts": [a.__dict__ for a in res.attempts], "ok": res.ok}
    if not res.ok:
        out["error"] = "no configured model answered (see attempts); set INSTINCT_* env or HF_TOKEN"
        return out
    r = res.result
    out.update(provider=r.provider, model=r.model, text=r.text, tool_calls=r.tool_calls)
    if execute and r.tool_calls:
        offered = {t["name"] for t in tools}
        out["tool_results"] = [call_tool(c["name"], c.get("arguments") or {}) if c.get("name") in offered
                               else {"error": f"model called {c.get('name')!r}, which was not offered"}
                               for c in r.tool_calls]
    return out


class SugarcodeDataset:
    """SugarCode's DomainDataset. Rows are synthetic queries whose answers were executed
    against the real modules and succeeded (sugarcode.llm.dataset.build), plus
    off-topic rows with no call. They contain no user data, so private=False; they are
    marked confirmed because each call was verified by execution, and meta says so."""
    product = PRODUCT

    def __init__(self, per_tool: int = 120, max_tools: int | None = None, seed: int = 0, off_topic_ratio: float = 0.125):
        self.per_tool, self.max_tools, self.seed, self.off_topic_ratio = per_tool, max_tools, seed, off_topic_ratio

    def rows(self) -> Iterable[ExampleRow]:
        from .dataset import build
        raw, _ = build(per_tool=self.per_tool, seed=self.seed, max_tools=self.max_tools)
        rng = random.Random(self.seed)
        pool = []
        for i, r in enumerate(raw):
            tools = json.loads(r["tools"]) if isinstance(r["tools"], str) else r["tools"]
            answers = json.loads(r["answers"]) if isinstance(r["answers"], str) else r["answers"]
            pool.append(tools)
            yield ExampleRow(query=r["query"], tools=tools, answers=answers, confirmed=True, private=False,
                             product=PRODUCT, source_ref=f"sugarcode.dataset.build#{i}",
                             meta={"origin": "synthetic, verified-executable"})
        n_off = max(1, round(len(raw) * self.off_topic_ratio / (1 - self.off_topic_ratio))) if raw else 0
        for j in range(n_off):
            yield ExampleRow(query=OFF_TOPIC[j % len(OFF_TOPIC)], tools=rng.choice(pool) if pool else [], answers=[],
                             confirmed=True, private=False, product=PRODUCT, source_ref=f"sugarcode.offtopic#{j}",
                             meta={"origin": "off-topic template"})


def build_shared_needle_dataset(out_path: str | Path, per_tool: int = 120, max_tools: int | None = None) -> dict:
    return build_needle_jsonl(SugarcodeDataset(per_tool=per_tool, max_tools=max_tools), out_path)
