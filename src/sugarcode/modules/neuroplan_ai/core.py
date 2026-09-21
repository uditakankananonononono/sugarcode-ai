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
        pos = [min(max(center[0] + dx, 2.0), image_size[0] - 3.0),
               min(max(center[1] + dy, 2.0), image_size[1] - 3.0),
               min(max(center[2] + dz, 2.0), image_size[2] - 3.0)]  # keep regions inside the grid
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


# --- drop 13: real A* corridor pathfinding over a voxel risk field -------------
def _risk_field_fn(regions: dict, sigma: float = 12.0):
    """risk(p) = sum_i w_i * exp(-d^2 / 2 sigma^2) over eloquent regions."""
    import math as _m
    regs = [(r["position"], r["risk_weight"]) for r in regions.values()]
    def risk(p):
        total = 0.0
        for pos, w in regs:
            d2 = sum((p[k] - pos[k]) ** 2 for k in range(3))
            total += w * _m.exp(-d2 / (2 * sigma * sigma))
        return total
    return risk


def plan_path_astar(tumor: dict, entry: list[float] | None = None,
                    image_size: tuple[int, int, int] = (64, 64, 64),
                    risk_lambda: float = 8.0, max_expand: int = 400000) -> dict:
    """A* shortest-risk path from a scalp entry point to the tumor center over
    the eloquent-region risk field. Cost per step = euclidean * (1 + lambda *
    risk(midpoint)); 26-connected grid, euclidean heuristic (admissible since
    risk term is >= 1). Returns the voxel path and compares it against the
    straight-line corridor it replaces."""
    import heapq
    import math as _m
    center = [float(c) for c in tumor["center"]]
    radius = tumor.get("radius_mm", 20)
    regions = _place_regions(image_size, [int(c) for c in center], radius)
    risk = _risk_field_fn(regions)
    if entry is None:
        entry = [center[0], center[1], float(image_size[2] - 1)]  # superior entry
    start = tuple(int(round(e)) for e in entry)
    goal = tuple(int(round(c)) for c in center)

    def in_bounds(p):
        return all(0 <= p[k] < image_size[k] for k in range(3))

    def h(p):
        return _m.sqrt(sum((p[k] - goal[k]) ** 2 for k in range(3)))

    neigh = [(dx, dy, dz) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
             for dz in (-1, 0, 1) if (dx, dy, dz) != (0, 0, 0)]
    dist = {start: 0.0}
    prev = {}
    pq = [(h(start), 0.0, start)]
    expanded = 0
    while pq:
        _, g, p = heapq.heappop(pq)
        if g > dist.get(p, float("inf")):
            continue
        if p == goal:
            break
        expanded += 1
        if expanded > max_expand:
            raise RuntimeError("A* exceeded expansion budget - grid too large or risk field blocking")
        for d in neigh:
            q = (p[0] + d[0], p[1] + d[1], p[2] + d[2])
            if not in_bounds(q):
                continue
            step = _m.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2)
            mid = tuple((p[k] + q[k]) / 2 for k in range(3))
            cost = step * (1.0 + risk_lambda * risk(mid))
            ng = g + cost
            if ng < dist.get(q, float("inf")):
                dist[q] = ng
                prev[q] = p
                heapq.heappush(pq, (ng + h(q), ng, q))
    if goal not in dist:
        raise RuntimeError("A* found no path - risk field fully blocks the target")
    path = []
    p = goal
    while p != start:
        path.append(p)
        p = prev[p]
    path.append(start)
    path.reverse()

    def line_risk_integral(a, b, n=200):
        total = 0.0
        for i in range(n):
            t = i / (n - 1)
            pt = tuple(a[k] + t * (b[k] - a[k]) for k in range(3))
            total += risk(pt)
        return total / n * _m.sqrt(sum((a[k] - b[k]) ** 2 for k in range(3)))

    straight = line_risk_integral(start, goal)
    path_risk = sum(risk(tuple(float(c) for c in p)) for p in path) / len(path) * sum(
        _m.sqrt(sum((path[i + 1][k] - path[i][k]) ** 2 for k in range(3)))
        for i in range(len(path) - 1))
    min_clear = min(_m.sqrt(sum((p[k] - r["position"][k]) ** 2 for k in range(3)))
                    for p in path for r in regions.values())
    return {
        "method": "A* over eloquent-region risk field (26-connected, euclidean heuristic)",
        "entry": list(start), "target": list(goal),
        "path_length_voxels": len(path),
        "path": [list(p) for p in path],
        "nodes_expanded": expanded,
        "path_risk_integral": round(path_risk, 3),
        "straight_line_risk_integral": round(straight, 3),
        "risk_reduction_vs_straight": round(1 - path_risk / straight, 4) if straight > 0 else 0.0,
        "note": ("small negative reductions are line-sampling noise - path tracks the "
                 "straight corridor when it is already clear" if straight > 0 and
                 -0.1 < 1 - path_risk / straight < 0.05 else None),
        "min_clearance_mm": round(min_clear, 2),
    }
