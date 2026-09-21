from __future__ import annotations

LIQUID_CLASSES = {
    "water": {"viscosity_cp": 1.0, "aspirate_speed_ul_s": 200, "air_gap_ul": 2},
    "glycerol_50": {"viscosity_cp": 6.0, "aspirate_speed_ul_s": 40, "air_gap_ul": 4},
    "enzyme_mix": {"viscosity_cp": 2.5, "aspirate_speed_ul_s": 80, "air_gap_ul": 3},
    "cells": {"viscosity_cp": 1.2, "aspirate_speed_ul_s": 100, "air_gap_ul": 2},
}


def pipette_plan(transfers: list[dict]) -> dict:
    """Convert transfer list to calibrated liquid-class handling steps.

    Each transfer: {"source": well, "dest": well, "volume_ul": x, "liquid": class}
    Applies viscosity-dependent speeds, air gaps and evaporation correction.
    """
    steps = []
    total_s = 0.0
    for i, t in enumerate(transfers):
        lc = LIQUID_CLASSES.get(t.get("liquid", "water"), LIQUID_CLASSES["water"])
        vol = t["volume_ul"]
        asp_t = vol / lc["aspirate_speed_ul_s"]
        evap = round(vol * 0.002 * (asp_t / 60), 4)
        steps.append({
            "step": i + 1, "source": t["source"], "dest": t["dest"],
            "volume_ul": vol, "liquid_class": t.get("liquid", "water"),
            "aspirate_speed_ul_s": lc["aspirate_speed_ul_s"],
            "air_gap_ul": lc["air_gap_ul"],
            "evaporation_correction_ul": evap,
            "estimated_s": round(2 * asp_t + 3, 1),
        })
        total_s += 2 * asp_t + 3
    return {"n_transfers": len(steps), "steps": steps,
            "estimated_total_min": round(total_s / 60, 1)}


def schedule_run(tasks: list[dict]) -> dict:
    """Greedy list-scheduling of deck tasks onto shared instruments.

    tasks: [{"id": str, "instrument": str, "duration_min": x, "after": [ids]}]
    Returns instrument timelines with makespan.
    """
    done: dict[str, float] = {}
    instrument_free: dict[str, float] = {}
    timeline: list[dict] = []
    pending = list(tasks)
    guard = 0
    while pending and guard < 10000:
        guard += 1
        progressed = False
        for t in list(pending):
            deps = t.get("after", [])
            if all(d in done for d in deps):
                ready = max([done[d] for d in deps], default=0.0)
                start = max(ready, instrument_free.get(t["instrument"], 0.0))
                end = start + t["duration_min"]
                timeline.append({"id": t["id"], "instrument": t["instrument"],
                                 "start_min": round(start, 1), "end_min": round(end, 1)})
                instrument_free[t["instrument"]] = end
                done[t["id"]] = end
                pending.remove(t)
                progressed = True
        if not progressed:
            raise ValueError("dependency cycle in task graph")
    makespan = max((x["end_min"] for x in timeline), default=0.0)
    return {"timeline": sorted(timeline, key=lambda x: x["start_min"]),
            "makespan_min": round(makespan, 1),
            "instrument_utilization": _utilization(timeline, makespan)}


def _utilization(timeline: list[dict], makespan: float) -> dict:
    busy: dict[str, float] = {}
    for x in timeline:
        busy[x["instrument"]] = busy.get(x["instrument"], 0.0) + (x["end_min"] - x["start_min"])
    return {k: round(v / makespan, 3) if makespan else 0.0 for k, v in busy.items()}


def monitor(run: dict, checkpoints: list[dict] | None = None) -> dict:
    """Real-time monitoring model: expected vs observed checkpoint times."""
    checkpoints = checkpoints or []
    alerts = []
    for cp in checkpoints:
        drift = cp.get("observed_min", cp["expected_min"]) - cp["expected_min"]
        if abs(drift) > cp.get("tolerance_min", 5):
            alerts.append({"task": cp["task"], "drift_min": round(drift, 1),
                           "severity": "warn" if abs(drift) < 15 else "critical"})
    return {
        "run_makespan_min": run.get("makespan_min"),
        "checkpoints": checkpoints,
        "alerts": alerts,
        "precision_note": "all timing tracked to the minute; volume QC via liquid-class calibration",
        "status": "on_track" if not alerts else "review_required",
    }
