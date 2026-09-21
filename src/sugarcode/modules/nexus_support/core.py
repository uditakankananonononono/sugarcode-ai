from __future__ import annotations

from omega.registry import REGISTRY

SUBNETWORK_OWNERS: dict[str, list[str]] = {}
for _slug, _spec in REGISTRY.items():
    SUBNETWORK_OWNERS.setdefault(_spec.subnetwork, []).append(_slug)

MODULE_TO_NET = {m: net for net, mods in SUBNETWORK_OWNERS.items() for m in mods}
SLA_HOURS = {"bug": 8, "feature": 72, "custom_build": 240, "question": 24, "integration": 48}

KEYWORDS = {
    "bug": ["error", "crash", "wrong", "fail", "bug", "broken", "traceback"],
    "custom_build": ["custom", "bespoke", "build", "tailor", "white-label"],
    "integration": ["integrate", "api", "pipeline", "connect", "deploy"],
    "feature": ["add", "support", "feature", "would like", "request"],
}


def triage(inquiry: str, module: str | None = None, tier: str = "startup") -> dict:
    """Classify, route to owning sub-network, estimate SLA, match knowledge base."""
    q = inquiry.lower()
    kind = next((k for k, kws in KEYWORDS.items() if any(w in q for w in kws)), "question")
    if kind == "feature" and "custom" in q:
        kind = "custom_build"
    target_module = module or next((m for m in MODULE_TO_NET if m.replace("_", " ") in q
                                    or m in q), None)
    network = MODULE_TO_NET.get(target_module, "platform")
    priority = {"bug": "high", "custom_build": "medium", "integration": "medium",
                "feature": "low", "question": "low"}[kind]
    sla = SLA_HOURS[kind] * (0.5 if tier == "enterprise" else 1.0)
    kb = _kb_match(kind, target_module)
    return {
        "classification": kind,
        "priority": priority,
        "routed_to": {"sub_network": network, "module": target_module},
        "sla_hours": sla,
        "tier_applied": tier,
        "kb_match": kb,
        "auto_resolvable": kb is not None and kind == "question",
        "escalation": ("human domain scientist on first response" if kind in ("bug", "custom_build")
                       else "auto-reply with KB, human on follow-up"),
    }


def _kb_match(kind, module):
    kb = {
        ("question", "crispr_opt"): "guide-scoring docs: GC 40-60%, NGG PAM, seed-region specificity",
        ("question", "virtual_cell"): "FBA model docs: stoichiometry, exchange fluxes, objective",
        ("question", "docking_studio"): "docking FAQ: pocket definition, score interpretation",
    }
    return kb.get((kind, module)) or (f"docs for {module}" if module else None)
