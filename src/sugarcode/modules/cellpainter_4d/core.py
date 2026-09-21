from __future__ import annotations
import math

EVENTS = {
    "differentiation": [
        (0.0, "baseline proliferative morphology"),
        (0.2, "cell-cycle exit - area increase begins"),
        (0.4, "process outgrowth / lineage marker onset"),
        (0.7, "mature morphology establishment"),
        (1.0, "terminal phenotype stable"),
    ],
    "apoptosis": [
        (0.0, "baseline"), (0.3, "membrane blebbing"), (0.5, "nuclear condensation"),
        (0.7, "cell shrinkage + fragmentation"), (1.0, "apoptotic bodies"),
    ],
    "emt": [
        (0.0, "epithelial cobblestone"), (0.25, "junction dissolution"),
        (0.5, "elongation begins"), (0.75, "mesenchymal spindle morphology"),
        (1.0, "migratory phenotype"),
    ],
}


def simulate_morphology(process: str, duration_h: float = 72.0, frames: int = 25) -> dict:
    """Temporal traces of morphology metrics through a dynamic process."""
    if process not in EVENTS:
        raise KeyError(f"unknown process {process!r}; have {sorted(EVENTS)}")
    events = EVENTS[process]
    traces = {"area": [], "circularity": [], "aspect_ratio": [], "intensity": []}
    timeline = []
    for f in range(frames):
        t = f / (frames - 1)
        hours = round(t * duration_h, 1)
        if process == "differentiation":
            area = 1.0 + 1.5 * t
            circ = 0.9 - 0.5 * t
            aspect = 1.0 + 3.0 * t
            inten = 1.0 + 0.3 * math.sin(4 * math.pi * t)
        elif process == "apoptosis":
            area = 1.0 - 0.7 * t ** 2
            circ = 0.85 + 0.1 * math.sin(10 * t)
            aspect = 1.0 + 0.2 * t
            inten = 1.0 + 0.8 * t
        else:  # emt
            area = 1.0 + 0.4 * t
            circ = 0.9 - 0.6 * t
            aspect = 1.0 + 2.5 * t ** 1.5
            inten = 1.0 - 0.2 * t
        traces["area"].append(round(area, 3))
        traces["circularity"].round if False else traces["circularity"].append(round(circ, 3))
        traces["aspect_ratio"].append(round(aspect, 3))
        traces["intensity"].append(round(inten, 3))
        timeline.append({"t_h": hours, "phase": _phase(events, t)})
    return {
        "process": process, "duration_h": duration_h,
        "event_timeline": [{"t_fraction": e[0], "event": e[1]} for e in events],
        "frames": timeline,
        "traces": traces,
        "morphological_drift": round(traces["area"][-1] - traces["area"][0], 3),
    }


def _phase(events: list, t: float) -> str:
    phase = events[0][1]
    for frac, name in events:
        if t >= frac:
            phase = name
    return phase
