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
    return _PROJECTS[-limit:][::-1]


def register_project(name: str, module: str, state: str = "created") -> dict:
    p = {"name": name, "module": module, "state": state}
    _PROJECTS.append(p)
    return p


def initiate_search(query: str, limit: int = 10) -> dict:
    """High-fidelity biological search across the module stack."""
    return biological_search(query, limit)
