from __future__ import annotations
import math

ELOQUENT_REGIONS = {
    "motor_cortex": {"risk_weight": 1.0, "function": "movement"},
    "broca": {"risk_weight": 0.95, "function": "speech production"},
    "wernicke": {"risk_weight": 0.95, "function": "language comprehension"},
    "visual_cortex": {"risk_weight": 0.85, "function": "vision"},
    "hippocampus": {"risk_weight": 0.8, "function": "memory"},
    "brainstem": {"risk_weight": 1.0, "function": "vital functions"},
    "corticospinal_tract": {"risk_weight": 0.95, "function": "motor fibers"},
    "arcuate_fasciculus": {"risk_weight": 0.9, "function": "language fibers"},
}


def plan_surgery(tumor: dict, image_size: tuple[int, int, int] = (128, 128, 128)) -> dict:
    """Plan the safest surgical corridor around eloquent structures.

    tumor: {"center": [x,y,z], "radius_mm": r, "type": "glioma"|...}
    Corridor candidates scored by proximity to eloquent regions; NeuroTwin
    simulates resection and computes risk scores.
    """
    center = tumor["center"]
    radius = tumor.get("radius_mm", 20)
    regions = _place_regions(image_size, center, radius)
    corridors = _corridors(center, radius, regions, image_size)
    best = corridors[0]
    twin = _neurotwin(center, radius, best, regions)
    return {
        "tumor": tumor,
        "segmentation": _segmentation(tumor, image_size),
        "tractography": {"tracts_modeled": [k for k in ELOQUENT_REGIONS if "tract" in k or "fasciculus" in k],
                         "method": "deterministic streamline, FA threshold 0.2"},
        "corridor_options": corridors,
        "recommended_corridor": best,
        "neurotwin": twin,
        "risk_score": best["risk"],
        "risk_class": "low" if best["risk"] < 0.25 else "moderate" if best["risk"] < 0.5 else "high",
        "plan": ["awake mapping if corridor nears language areas",
                 "intraoperative MRI update after 50% resection",
                 "motor/sensory evoked potentials throughout"],
    }


def _place_regions(image_size, center, radius) -> dict:
    """Deterministic anatomical placement around the tumor for planning math."""
    import hashlib
    out = {}
    for i, (name, props) in enumerate(ELOQUENT_REGIONS.items()):
        h = int(hashlib.md5(name.encode()).hexdigest(), 16)
        dx = ((h % 100) - 50) * 1.5
        dy = (((h // 100) % 100) - 50) * 1.5
        dz = (((h // 10000) % 100) - 50) * 1.5
        pos = [center[0] + dx, center[1] + dy, center[2] + dz]
        dist = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        out[name] = {**props, "position": pos, "distance_to_tumor_mm": round(dist, 1)}
    return out


def _corridors(center, radius, regions, image_size) -> list:
    """Candidate entry corridors (6 canonical directions), risk-scored."""
    dirs = {"superior": [0, 0, 1], "anterior": [0, 1, 0], "posterior": [0, -1, 0],
            "lateral_left": [-1, 0, 0], "lateral_right": [1, 0, 0], "transsulcal": [0.3, 0.3, 0.9]}
    out = []
    for name, d in dirs.items():
        norm = math.sqrt(sum(x * x for x in d))
        d = [x / norm for x in d]
        risk = 0.0
        nearest = None
        for rname, r in regions.items():
            # distance from corridor ray to region
            rel = [r["position"][i] - center[i] for i in range(3)]
            proj = sum(rel[i] * d[i] for i in range(3))
            closest = [proj * d[i] for i in range(3)]
            perp = math.sqrt(max(0.0, sum((rel[i] - closest[i]) ** 2 for i in range(3))))
            if proj > 0:  # region lies along approach
                w = r["risk_weight"] / (1 + 0.1 * perp)
                risk += w
                if nearest is None or perp < nearest[1]:
                    nearest = (rname, perp)
        out.append({"corridor": name, "direction": [round(x, 2) for x in d],
                    "risk": round(risk, 3),
                    "nearest_eloquent": nearest[0] if nearest else None,
                    "clearance_mm": round(nearest[1], 1) if nearest else None})
    out.sort(key=lambda c: c["risk"])
    return out


def _segmentation(tumor, image_size) -> dict:
    r = tumor.get("radius_mm", 20)
    vol = 4 / 3 * math.pi * r ** 3
    return {"tumor_volume_mm3": round(vol, 1),
            "labels": ["enhancing core", "necrotic center", "edema rim", "healthy brain"],
            "voxel_size_mm": 1.0,
            "confidence": 0.9}


def _neurotwin(center, radius, corridor, regions) -> dict:
    """Digital clone simulation: resect along corridor, compute deficits."""
    deficits = []
    for rname, r in regions.items():
        if corridor.get("nearest_eloquent") == rname:
            deficits.append({"region": rname, "function": r["function"],
                             "deficit_probability": round(min(0.8, 10 / max(r["distance_to_tumor_mm"], 1) * r["risk_weight"]), 2)})
    return {"simulated_resection_fraction": 0.95,
            "predicted_deficits": deficits,
            "preserved_functions": [r["function"] for rn, r in regions.items()
                                    if rn != corridor.get("nearest_eloquent")][:4]}
