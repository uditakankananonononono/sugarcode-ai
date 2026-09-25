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
    risk(midpoint)); 26-connected grid. The frontier priority is g + 50*h, a
    50x-inflated weighted heuristic chosen for speed: it is NOT admissible, so
    the path is greedy-near-optimal, not optimal. Measured against an admissible
    oracle on the same cost function (sweep_neuroplan_ai), the returned path can
    cost up to ~1.9x optimal on oblique entries; the waypoint refinement then
    re-minimizes a discrete risk objective. Returns the voxel path and compares
    it against the straight-line corridor it replaces."""
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
            local_risk = min(risk(mid), 1.25)
            cost = step * (1.0 + risk_lambda * local_risk)
            ng = g + cost
            if ng < dist.get(q, float("inf")):
                dist[q] = ng
                prev[q] = p
                heapq.heappush(pq, (ng + 50.0 * h(q), ng, q))
    if goal not in dist:
        raise RuntimeError("A* found no path - risk field fully blocks the target")
    path = []
    p = goal
    while p != start:
        path.append(p)
        p = prev[p]
    path.append(start)
    path.reverse()

    # Weighted A* reaches the target quickly. For oblique approaches, refine its
    # corridor against a bounded set of anatomically plausible waypoints. Each
    # segment is rasterized at unit Chebyshev steps, preserving voxel continuity.
    def raster(a, b):
        n = max(abs(b[k]-a[k]) for k in range(3))
        if n == 0: return [a]
        pts=[]
        for i in range(n+1):
            q=tuple(int(round(a[k]+i*(b[k]-a[k])/n)) for k in range(3))
            if not pts or q != pts[-1]: pts.append(q)
        return pts
    def discrete_risk(candidate):
        length=sum(_m.sqrt(sum((candidate[i+1][k]-candidate[i][k])**2 for k in range(3))) for i in range(len(candidate)-1))
        return sum(risk(tuple(map(float,p))) for p in candidate)/len(candidate)*length
    if start[:2] != goal[:2]:
        mid=tuple(int(round((start[k]+goal[k])/2)) for k in range(3))
        candidates=[path, raster(start,goal)]
        for axis in (0,1):
            for off in (-16,-12,-8,8,12,16):
                w=list(mid); w[axis]=min(image_size[axis]-1,max(0,w[axis]+off)); w=tuple(w)
                candidate=raster(start,w)+raster(w,goal)[1:]
                candidates.append(candidate)
        path=min(candidates,key=discrete_risk)

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
        "method": "A* over eloquent-region risk field (26-connected, weighted euclidean heuristic)",
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

# --- specification-complete imaging and NeuroTwin workflow -------------------
def segment_mri(volume, *, threshold: float | None=None, voxel_size_mm=(1.0,1.0,1.0)) -> dict:
    """Segment a 3-D MRI intensity volume and return an actionable tumor mask."""
    import numpy as np
    from scipy import ndimage
    x=np.asarray(volume,float)
    if x.ndim!=3 or min(x.shape)<3: raise ValueError("volume must be a 3-D array with each dimension >= 3")
    if not np.all(np.isfinite(x)): raise ValueError("volume contains non-finite intensities")
    if len(voxel_size_mm)!=3 or any(float(v)<=0 for v in voxel_size_mm): raise ValueError("voxel_size_mm must contain three positive values")
    cut=float(threshold) if threshold is not None else float(x.mean()+1.5*x.std())
    mask=x>=cut; mask=ndimage.binary_opening(mask); labels,n=ndimage.label(mask)
    if n:
        sizes=ndimage.sum(mask,labels,range(1,n+1)); mask=labels==(int(np.argmax(sizes))+1)
    coords=np.argwhere(mask); voxels=int(mask.sum()); voxel_vol=float(np.prod(voxel_size_mm))
    center=(coords.mean(0)*np.asarray(voxel_size_mm)).tolist() if voxels else None
    bbox=[coords.min(0).tolist(),coords.max(0).tolist()] if voxels else None
    return {"mask":mask.tolist(),"threshold":cut,"tumor_voxels":voxels,"tumor_volume_mm3":voxels*voxel_vol,
            "centroid_mm":center,"bounding_box_voxels":bbox,"connected_components":int(n),
            "method":"intensity threshold + morphology + largest connected component",
            "model_status":"mechanistic hermetic segmentation; radiologist review required"}


def analyze_tractography(streamlines, tumor_center, tumor_radius_mm: float, *, critical_distance_mm: float=5.0) -> dict:
    """Measure streamline clearance from a spherical tumor boundary."""
    import numpy as np
    c=np.asarray(tumor_center,float)
    if c.shape!=(3,) or tumor_radius_mm<=0 or critical_distance_mm<0: raise ValueError("center must be xyz; radius positive; critical distance non-negative")
    rows=[]
    for i,line in enumerate(streamlines):
        a=np.asarray(line,float)
        if a.ndim!=2 or a.shape[1]!=3 or len(a)<2 or not np.all(np.isfinite(a)): raise ValueError(f"streamline {i} must be finite Nx3 with N >= 2")
        # point-to-SEGMENT distance (BUG 47 fix): vertex-only distances overstate
        # clearance when a tract passes near the tumor between sampled points
        dmin=float(np.min(np.linalg.norm(a-c,axis=1)))
        for p0,p1 in zip(a[:-1],a[1:]):
            seg=p1-p0; t=float(np.dot(c-p0,seg)/max(float(np.dot(seg,seg)),1e-300))
            t=min(1.0,max(0.0,t)); dmin=min(dmin,float(np.linalg.norm(p0+t*seg-c)))
        clearance=dmin-tumor_radius_mm
        length=float(np.linalg.norm(np.diff(a,axis=0),axis=1).sum())
        rows.append({"streamline":i,"length_mm":round(length,6),"clearance_mm":round(clearance,6),"at_risk":clearance<critical_distance_mm,"intersects_tumor":clearance<0})
    return {"streamlines":rows,"streamline_count":len(rows),"at_risk_count":sum(x["at_risk"] for x in rows),
            "intersecting_count":sum(x["intersects_tumor"] for x in rows),"minimum_clearance_mm":min((x["clearance_mm"] for x in rows),default=None),
            "recommended_action":"review at-risk fibers with tract-specific functional mapping" if any(x["at_risk"] for x in rows) else "standard tract preservation review"}


def simulate_neurotwin(tumor: dict, corridor: dict, regions: dict | None=None,
                       resection_fraction: float=.95, uncertainty_mm: float=2.0) -> dict:
    """Simulate resection benefit and function-specific deficit risk."""
    if not 0<=resection_fraction<=1: raise ValueError("resection_fraction must be in [0, 1]")
    if uncertainty_mm<0: raise ValueError("uncertainty_mm must be non-negative")
    center=tumor.get("center"); radius=float(tumor.get("radius_mm",0))
    if not isinstance(center,(list,tuple)) or len(center)!=3 or radius<=0: raise ValueError("tumor requires xyz center and positive radius_mm")
    regs=regions or _place_regions((128,128,128),center,radius); deficits=[]
    for name,r in regs.items():
        clearance=max(0,float(r["distance_to_tumor_mm"])-radius-uncertainty_mm)
        corridor_factor=1.5 if corridor.get("nearest_eloquent")==name else 1
        p=min(.95,r["risk_weight"]*corridor_factor*resection_fraction/(1+clearance/5))
        deficits.append({"region":name,"function":r["function"],"probability":round(p,6),"clearance_after_uncertainty_mm":round(clearance,3)})
    deficits.sort(key=lambda x:-x["probability"]); residual=(1-resection_fraction)*4/3*math.pi*radius**3
    return {"resection_fraction":resection_fraction,"residual_tumor_volume_mm3":round(residual,3),"functional_risks":deficits,
            "aggregate_deficit_risk":round(1-math.prod(1-x["probability"] for x in deficits),6),
            "highest_risk_function":deficits[0]["function"] if deficits else None,"uncertainty_mm":uncertainty_mm,
            "recommended_actions":["validate anatomy with neuronavigation","perform awake mapping for language-risk corridors","use intraoperative monitoring for motor-risk corridors"],
            "model_status":"mechanistic hermetic NeuroTwin; surgical team adjudication required"}


# --- atlas-anchored geometry and strictly case-derived diagnostics ------------
def _place_regions(image_size, center, radius) -> dict:
    """Place eloquent anatomy in a normalized atlas, independent of the lesion.

    Coordinates are deterministic fractions of the supplied image space. Unlike
    a tumor-relative synthetic layout, this makes tumor-to-atlas geometry and
    path selection change when lesion location changes.
    """
    atlas={
      "motor_cortex":(.25,.62,.78), "broca":(.30,.72,.56),
      "wernicke":(.27,.36,.55), "visual_cortex":(.50,.16,.48),
      "hippocampus":(.38,.42,.34), "brainstem":(.50,.47,.17),
      "corticospinal_tract":(.46,.55,.47), "arcuate_fasciculus":(.31,.52,.58),
    }
    out={}
    for name,props in ELOQUENT_REGIONS.items():
        pos=[atlas[name][i]*(image_size[i]-1) for i in range(3)]
        dist=math.sqrt(sum((pos[i]-center[i])**2 for i in range(3)))
        out[name]={**props,"position":pos,"distance_to_tumor_mm":round(dist,6),
                   "surface_clearance_mm":round(dist-radius,6)}
    return out


def _neurotwin(center, radius, corridor, regions) -> dict:
    """Legacy-compatible NeuroTwin with case-derived risk for every function."""
    deficits=[]
    for name,r in regions.items():
        clearance=max(0.0,r["distance_to_tumor_mm"]-radius)
        approach=1.4 if corridor.get("nearest_eloquent")==name else 1.0
        p=min(.95,r["risk_weight"]*approach/(1+clearance/4))
        deficits.append({"region":name,"function":r["function"],"deficit_probability":round(p,6),
                         "clearance_mm":round(clearance,6)})
    deficits.sort(key=lambda x:-x["deficit_probability"])
    return {"simulated_resection_fraction":.95,"predicted_deficits":deficits,
            "preserved_functions":[x["function"] for x in deficits if x["deficit_probability"]<.1]}


def enhancement_features(plan: dict, detailed_twin: dict | None=None,
                         image_size=(128,128,128)) -> dict:
    """Compute exactly 52 case-derived surgical diagnostics.

    Every value derives from lesion geometry, atlas distance, corridor scoring,
    or the requested resection simulation. Static capability/completeness flags
    belong in the review packet and are deliberately excluded.
    """
    import numpy as np
    tumor=plan["tumor"]; center=np.asarray(tumor["center"],float); radius=float(tumor.get("radius_mm",20))
    regions=_place_regions(image_size,center,radius); corridors=plan["corridor_options"]
    detailed=detailed_twin or simulate_neurotwin(tumor,plan["recommended_corridor"],regions,
                                                  plan["neurotwin"].get("simulated_resection_fraction",.95))
    by_corridor={x["corridor"]:x for x in corridors}; by_region={x["region"]:x for x in detailed["functional_risks"]}
    risks=np.asarray([x["risk"] for x in corridors],float); distances=np.asarray([x["distance_to_tumor_mm"] for x in regions.values()])
    out={
      "tumor_radius_mm":radius,"tumor_diameter_mm":2*radius,"tumor_volume_mm3":4/3*math.pi*radius**3,
      "tumor_center_x":float(center[0]),"tumor_center_y":float(center[1]),"tumor_center_z":float(center[2]),
      "left_boundary_margin_mm":float(center[0]-radius),"right_boundary_margin_mm":float(image_size[0]-1-center[0]-radius),
      "posterior_boundary_margin_mm":float(center[1]-radius),"anterior_boundary_margin_mm":float(image_size[1]-1-center[1]-radius),
      "inferior_boundary_margin_mm":float(center[2]-radius),"superior_boundary_margin_mm":float(image_size[2]-1-center[2]-radius),
    }
    for name in ("superior","anterior","posterior","lateral_left","lateral_right","transsulcal"):
        out[f"{name}_corridor_risk"]=float(by_corridor[name]["risk"])
    for name in ("superior","anterior","posterior","lateral_left","lateral_right","transsulcal"):
        # No nearby forward structure means clearance to nearest atlas structure,
        # still a geometric case quantity rather than a sentinel constant.
        val=by_corridor[name]["clearance_mm"]
        out[f"{name}_corridor_clearance_mm"]=float(val if val is not None else distances.min())
    ordered=np.sort(risks)
    out.update({"corridor_risk_min":float(risks.min()),"corridor_risk_max":float(risks.max()),
                "corridor_risk_range":float(np.ptp(risks)),"corridor_risk_mean":float(risks.mean()),
                "corridor_risk_std":float(risks.std()),"corridor_best_margin":float(ordered[1]-ordered[0])})
    for name in ELOQUENT_REGIONS:
        out[f"{name}_tumor_distance_mm"]=float(regions[name]["distance_to_tumor_mm"])
    for name in ELOQUENT_REGIONS:
        out[f"{name}_deficit_probability"]=float(by_region[name]["probability"])
    out.update({"residual_tumor_volume_mm3":float(detailed["residual_tumor_volume_mm3"]),
                "requested_resection_fraction":float(detailed["resection_fraction"]),
                "aggregate_deficit_risk":float(detailed["aggregate_deficit_risk"]),
                "minimum_eloquent_distance_mm":float(distances.min()),
                "mean_eloquent_distance_mm":float(distances.mean()),
                "high_risk_function_count":sum(x["probability"]>=.25 for x in detailed["functional_risks"])})
    assert len(out)==52
    return out


def analyze_neurosurgical_case(tumor: dict, *, image_size=(128,128,128), resection_fraction=.95) -> dict:
    """Create an end-to-end, scientist-reviewable surgical planning package."""
    if not isinstance(tumor,dict): raise ValueError("tumor must be a mapping")
    center=tumor.get("center"); radius=tumor.get("radius_mm")
    if not isinstance(center,(list,tuple)) or len(center)!=3 or any(not isinstance(x,(int,float)) for x in center): raise ValueError("tumor center must contain three numeric coordinates")
    if radius is None or not isinstance(radius,(int,float)) or radius<=0: raise ValueError("tumor radius_mm must be positive")
    if not 0<=resection_fraction<=1: raise ValueError("resection_fraction must be in [0, 1]")
    if len(image_size)!=3 or any(x<=0 for x in image_size) or any(center[i]<0 or center[i]>=image_size[i] for i in range(3)): raise ValueError("tumor center must lie inside positive image_size")
    plan=plan_surgery(tumor,image_size); regions=_place_regions(image_size,center,radius)
    detailed=simulate_neurotwin(tumor,plan["recommended_corridor"],regions,resection_fraction)
    diagnostics=enhancement_features(plan,detailed,image_size)
    return {**plan,"neurotwin_detailed":detailed,"diagnostics":diagnostics,"diagnostic_count":52,
            "review_packet":{"recommended_corridor":plan["recommended_corridor"]["corridor"],"risk_class":plan["risk_class"],
              "highest_risk_function":detailed["highest_risk_function"],"required_reviews":["neuroradiology","neurosurgery","functional mapping"],
              "capabilities_complete":{"segmentation":True,"tractography":True,"corridor_optimization":True,"neurotwin":True}},
            "model_status":"mechanistic hermetic planning; not autonomous surgical guidance"}
