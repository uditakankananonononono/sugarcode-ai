from __future__ import annotations
import statistics
import time
from omega.registry import REGISTRY

_METRICS: list[dict] = []


def record(module: str, metric: str, value: float, kind: str = "accuracy") -> dict:
    """Record one metric observation (accuracy | efficiency | throughput | latency)."""
    if module not in REGISTRY:
        raise KeyError(f"unknown module {module!r}")
    m = {"module": module, "metric": metric, "value": float(value),
         "kind": kind, "ts": time.time()}
    _METRICS.append(m)
    return m


def stats(kind: str | None = None) -> dict:
    """Global precision view: per-metric aggregates across the platform."""
    rows = [m for m in _METRICS if kind is None or m["kind"] == kind]
    grouped: dict[str, list[float]] = {}
    for m in rows:
        grouped.setdefault(f"{m['module']}:{m['metric']}:{m['kind']}", []).append(m["value"])
    series = []
    for key, vals in grouped.items():
        module, metric, k = key.split(":", 2)
        series.append({
            "module": module, "metric": metric, "kind": k,
            "n": len(vals), "mean": round(statistics.fmean(vals), 5),
            "stdev": round(statistics.pstdev(vals), 5) if len(vals) > 1 else 0.0,
            "min": round(min(vals), 5), "max": round(max(vals), 5),
        })
    return {"observations": len(rows), "series": series}


def subnetwork_rollup() -> dict:
    """Per-sub-network aggregates: the dashboard's global precision view."""
    base = stats()
    by_sn: dict[str, dict] = {}
    for s in base["series"]:
        sn = REGISTRY[s["module"]].subnetwork
        d = by_sn.setdefault(sn, {"kinds": set(), "metrics": 0, "mean_values": []})
        d["kinds"].add(s["kind"])
        d["metrics"] += 1
        d["mean_values"].append(s["mean"])
    return {
        sn: {"kinds": sorted(d["kinds"]), "metric_series": d["metrics"],
             "mean_of_means": round(sum(d["mean_values"]) / len(d["mean_values"]), 5)
             if d["mean_values"] else 0.0}
        for sn, d in by_sn.items()
    }
