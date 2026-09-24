"""Expose SugarCode module functions as LLM tools (OpenAI function-calling schema).

The catalog is built by introspecting each registered module's public,
documented functions. Only functions whose parameters are all JSON-typed
(str/int/float/bool/list/dict and their Optional forms) are exposed, so the
model can call them with plain JSON and nothing else is reachable.
"""
from __future__ import annotations

import importlib
import inspect
import json
import math
from dataclasses import dataclass
from functools import lru_cache

_JSON_TYPES = {
    "str": {"type": "string"}, "int": {"type": "integer"}, "float": {"type": "number"},
    "bool": {"type": "boolean"}, "list": {"type": "array"}, "dict": {"type": "object"},
    "list[str]": {"type": "array", "items": {"type": "string"}},
    "list[float]": {"type": "array", "items": {"type": "number"}},
    "list[int]": {"type": "array", "items": {"type": "integer"}},
    "list[dict]": {"type": "array", "items": {"type": "object"}},
    "dict[str, float]": {"type": "object", "additionalProperties": {"type": "number"}},
}


def _schema_for(annotation) -> dict | None:
    s = annotation if isinstance(annotation, str) else getattr(annotation, "__name__", str(annotation))
    s = s.replace("typing.", "").replace("'", "").strip()
    optional = False
    if s.startswith("Optional[") and s.endswith("]"):
        s, optional = s[9:-1], True
    elif s.endswith("| None"):
        s, optional = s[:-6].strip(), True
    base = _JSON_TYPES.get(s)
    if base is None:
        return None
    return dict(base, **({"nullable": True} if optional else {}))


@dataclass(frozen=True)
class Tool:
    name: str            # "<module>__<function>"
    module: str
    function: str
    description: str
    parameters: dict

    def openai_schema(self) -> dict:
        return {"type": "function", "function": {
            "name": self.name, "description": self.description, "parameters": self.parameters}}


def _describe(fn) -> str:
    doc = inspect.getdoc(fn) or ""
    first = doc.strip().split("\n\n")[0].replace("\n", " ")
    return first[:600]


def _tool_from(module: str, fname: str, fn) -> Tool | None:
    if not inspect.isfunction(fn) or not fn.__doc__:
        return None
    sig = inspect.signature(fn)
    props, required = {}, []
    for p in sig.parameters.values():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            return None
        if p.annotation is inspect._empty:
            return None
        sch = _schema_for(p.annotation)
        if sch is None:
            return None
        if p.default is inspect._empty:
            required.append(p.name)
        elif isinstance(p.default, (str, int, float, bool)) or p.default is None:
            sch = dict(sch, default=p.default)
        props[p.name] = sch
    return Tool(name=f"{module}__{fname}", module=module, function=fname,
                description=_describe(fn),
                parameters={"type": "object", "properties": props, "required": required})


@lru_cache(maxsize=1)
def catalog() -> dict[str, Tool]:
    """All exposable tools keyed by tool name."""
    from omega.registry import module_slugs
    out: dict[str, Tool] = {}
    for slug in sorted(module_slugs()):
        try:
            mod = importlib.import_module(f"sugarcode.modules.{slug}")
        except Exception:  # a module failing to import must not take the catalog down
            continue
        names = getattr(mod, "__all__", None) or [n for n in dir(mod) if not n.startswith("_")]
        for n in names:
            fn = getattr(mod, n, None)
            if getattr(fn, "__module__", "").startswith(f"sugarcode.modules.{slug}"):
                t = _tool_from(slug, n, fn)
                if t:
                    out[t.name] = t
    return out


def tools_for_modules(modules: list[str], limit: int = 24) -> list[Tool]:
    """Tools belonging to the given modules, in module order, capped at `limit`."""
    cat = catalog()
    picked: list[Tool] = []
    for m in modules:
        picked.extend(t for t in cat.values() if t.module == m)
    return picked[:limit]


def _jsonable(x, depth: int = 0):
    if depth > 8:
        return str(x)
    if isinstance(x, (str, bool)) or x is None:
        return x
    if isinstance(x, int):
        return x
    if isinstance(x, float):
        return x if math.isfinite(x) else str(x)
    if isinstance(x, dict):
        return {str(k): _jsonable(v, depth + 1) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [_jsonable(v, depth + 1) for v in x]
    try:
        import numpy as np
        if isinstance(x, np.ndarray):
            return _jsonable(x.tolist(), depth + 1)
        if isinstance(x, np.generic):
            return _jsonable(x.item(), depth + 1)
    except ImportError:
        pass
    if hasattr(x, "__dict__"):
        return _jsonable(vars(x), depth + 1)
    return str(x)


def call_tool(name: str, arguments: dict | str) -> dict:
    """Execute one catalog tool. Never raises: errors come back as {"error": ...}."""
    cat = catalog()
    if name not in cat:
        return {"error": f"unknown tool {name!r}"}
    t = cat[name]
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments or "{}")
        except json.JSONDecodeError as e:
            return {"error": f"arguments are not valid JSON: {e}"}
    allowed = set(t.parameters["properties"])
    extra = set(arguments) - allowed
    if extra:
        return {"error": f"unexpected arguments {sorted(extra)}; allowed {sorted(allowed)}"}
    missing = [r for r in t.parameters["required"] if r not in arguments]
    if missing:
        return {"error": f"missing required arguments {missing}"}
    fn = getattr(importlib.import_module(f"sugarcode.modules.{t.module}"), t.function)
    try:
        result = fn(**arguments)
    except Exception as e:  # surface the module's own validation message to the model
        return {"error": f"{type(e).__name__}: {e}"}
    out = _jsonable(result)
    text = json.dumps(out)
    if len(text) > 12000:
        return {"result_truncated": True, "result_preview": text[:12000]}
    return {"result": out}
