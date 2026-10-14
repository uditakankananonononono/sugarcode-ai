"""Row 272 Myth Creation (PARTIAL): deterministic construction of a foundational-story skeleton from caller-supplied
phenomena to explain, agents (deities or ancestors) and optional 'must come first' dependencies.
Computed: a dependency-respecting creation order (topological sort, hash-ranked ties), balanced agent assignment,
and a seeded choice of act and motive from fixed small vocabularies, with an input fingerprint.
Not computed: literary quality, originality, cultural authenticity or any claim about real mythologies."""
from __future__ import annotations
import hashlib
import json

MAX_PHENOMENA = 30
MAX_AGENTS = 12
MAX_NAME = 48
MAX_SEED = 2 ** 63 - 1
ACTS = ("shaped", "sang into being", "tore from the dark", "wove", "divided from the waters", "breathed life into")
MOTIVES = ("out of loneliness", "in anger", "as a gift", "to end a quarrel", "by a sworn bargain", "in grief")
STATUS_NOTE = ("PARTIAL: structural myth skeleton from supplied names, seeded vocabulary choices and dependency "
               "ordering; no literary quality, originality or cultural-authenticity judgement")


def _rank(seed, kind, name):
    return int(hashlib.sha256(f"{seed}:{kind}:{name}".encode("utf-8")).hexdigest(), 16)


def _names(v, name, cap):
    if not isinstance(v, (list, tuple)) or not 1 <= len(v) <= cap:
        raise ValueError(f"{name}: list of 1..{cap} names required")
    out = []
    for i, x in enumerate(v):
        if not isinstance(x, str):
            raise ValueError(f"{name}[{i}]: str required")
        s = x.strip()
        if not s or len(s) > MAX_NAME:
            raise ValueError(f"{name}[{i}]: 1..{MAX_NAME} characters after trimming required")
        out.append(s)
    if len(set(out)) != len(out):
        raise ValueError(f"{name}: names must be unique")
    return out


def _deps(v, phenomena):
    if v is None:
        return {p: [] for p in phenomena}
    if not isinstance(v, dict):
        raise ValueError("dependencies: dict of phenomenon -> list of prerequisite phenomena required")
    out = {p: [] for p in phenomena}
    for k, pre in v.items():
        if not isinstance(k, str) or k.strip() not in out:
            raise ValueError(f"dependencies: unknown phenomenon {k!r}")
        if not isinstance(pre, (list, tuple)):
            raise ValueError(f"dependencies[{k!r}]: list required")
        for q in pre:
            if not isinstance(q, str) or q.strip() not in out:
                raise ValueError(f"dependencies[{k!r}]: unknown prerequisite {q!r}")
            if q.strip() == k.strip():
                raise ValueError(f"dependencies[{k!r}]: a phenomenon cannot precede itself")
        out[k.strip()] = sorted({q.strip() for q in pre})
    return out


def create_myth(phenomena, agents, seed=0, dependencies=None):
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed <= MAX_SEED:
        raise ValueError(f"seed: int in [0, {MAX_SEED}] required")
    ph, ag = _names(phenomena, "phenomena", MAX_PHENOMENA), _names(agents, "agents", MAX_AGENTS)
    deps = _deps(dependencies, ph)
    remaining = {p: set(deps[p]) for p in ph}
    order = []
    while remaining:
        ready = sorted((p for p, d in remaining.items() if not d), key=lambda p: (_rank(seed, "order", p), p))
        if not ready:
            raise ValueError("dependencies: cycle detected, no creation order exists")
        nxt = ready[0]
        order.append(nxt)
        del remaining[nxt]
        for d in remaining.values():
            d.discard(nxt)
    ranked = sorted(ag, key=lambda a: (_rank(seed, "agent", a), a))
    story, load = [], {a: 0 for a in ag}
    for i, p in enumerate(order):
        a = ranked[i % len(ranked)]
        act = ACTS[_rank(seed, "act", p) % len(ACTS)]
        motive = MOTIVES[_rank(seed, "motive", p) % len(MOTIVES)]
        load[a] += 1
        after = deps[p]
        line = f"{a} {act} {p} {motive}" + (f", once {', '.join(after)} existed" if after else "") + "."
        story.append({"step": i + 1, "phenomenon": p, "agent": a, "act": act, "motive": motive,
                      "after": list(after), "line": line})
    fp = hashlib.sha256(json.dumps([ph, ag, seed, deps], sort_keys=True).encode("utf-8")).hexdigest()
    return {"order": order, "story": story, "agent_load": load,
            "load_spread": max(load.values()) - min(load.values()), "narrative": " ".join(s["line"] for s in story),
            "seed": seed, "input_fingerprint": fp, "status_note": STATUS_NOTE}
