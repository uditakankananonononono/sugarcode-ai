"""Platform health: import checks and self-tests across the module stack."""
from __future__ import annotations
import importlib
import time
from .registry import REGISTRY


def module_health(slug: str) -> dict:
    spec = REGISTRY[slug]
    t0 = time.perf_counter()
    try:
        mod = importlib.import_module(f"sugarcode.modules.{slug}")
        callables = sorted(n for n in dir(mod) if not n.startswith("_"))
        ok = bool(callables)
        detail = f"{len(callables)} public callables" if ok else "no public callables"
    except ModuleNotFoundError:
        ok, callables, detail = False, [], "implementation package not present"
    except Exception as exc:  # import-time error
        ok, callables, detail = False, [], f"import error: {exc}"
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    try:  # feed Omega Stats with every health probe
        from sugarcode.modules.omega_stats import record
        record(slug, "import_latency_ms", latency_ms, kind="latency")
    except Exception:
        pass  # metrics must never break a health check
    return {
        "slug": slug, "name": spec.name, "subnetwork": spec.subnetwork,
        "status": spec.status, "importable": ok, "detail": detail,
        "latency_ms": latency_ms,
    }


def compute_flux() -> dict:
    """Global compute flux: health across all 95 registered modules, grouped by sub-network."""
    results = [module_health(s) for s in REGISTRY]
    by_sn: dict[str, dict] = {}
    for r in results:
        d = by_sn.setdefault(r["subnetwork"], {"total": 0, "online": 0})
        d["total"] += 1
        d["online"] += 1 if r["importable"] else 0
    return {
        "modules_total": len(results),
        "modules_online": sum(1 for r in results if r["importable"]),
        "subnetworks": {k: {**v, "flux": round(v["online"] / v["total"], 3)}
                        for k, v in by_sn.items()},
        "modules": results,
    }
