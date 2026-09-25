from __future__ import annotations
from omega.health import compute_flux
from omega.search import biological_search

_PROJECTS: list[dict] = []  # in-memory project state store


def dashboard() -> dict:
    """Unified platform view: compute flux, sub-network status, project states."""
    flux = compute_flux()
    return {
        "platform": "SugarCode AI / Omega OS v7.0",
        "compute_flux": {
            "modules_online": flux["modules_online"],
            "modules_total": flux["modules_total"],
            "global_flux": round(flux["modules_online"] / flux["modules_total"], 3),
        },
        "subnetworks": flux["subnetworks"],
        "recent_projects": recent_projects(),
        "alerts": _alerts(flux),
    }


def _alerts(flux: dict) -> list[str]:
    return [f"{len([m for m in flux['modules'] if not m['importable']])} modules pending implementation"
            ] if any(not m["importable"] for m in flux["modules"]) else []


def recent_projects(limit: int = 10) -> list[dict]:
    """Most recent projects first.  limit=0 returns [] (the old slice
    _PROJECTS[-0:] returned every project); negative limits are rejected."""
    if limit < 0:
        raise ValueError(f"limit must be >= 0, got {limit}")
    if limit == 0:
        return []
    return _PROJECTS[-limit:][::-1]


def register_project(name: str, module: str, state: str = "created") -> dict:
    """Register a project against a real registry module slug."""
    from omega.registry import REGISTRY
    if not isinstance(name, str) or not name.strip():
        raise ValueError("project name must be a non-empty string")
    if module not in REGISTRY:
        raise ValueError(f"unknown module slug {module!r}; must be one of the "
                         f"{len(REGISTRY)} registered modules")
    p = {"name": name.strip(), "module": module, "state": state}
    _PROJECTS.append(p)
    return p


def initiate_search(query: str, limit: int = 10) -> dict:
    """High-fidelity biological search across the module stack."""
    return biological_search(query, limit)
