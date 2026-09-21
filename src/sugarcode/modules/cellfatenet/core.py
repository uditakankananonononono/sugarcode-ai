from __future__ import annotations

# Small curated lineage GRN: node -> {regulator: sign}
LINEAGE_GRN = {
    "OCT4": {"targets": {"SOX2": "+", "NANOG": "+", "MYOD1": "-", "GATA4": "-"}},
    "SOX2": {"targets": {"OCT4": "+", "NANOG": "+", "ASCL1": "-"}},
    "NANOG": {"targets": {"OCT4": "+", "GATA4": "-"}},
    "GATA4": {"targets": {"MEF2C": "+", "TBX5": "+", "OCT4": "-"}},
    "MEF2C": {"targets": {"TNNT2": "+", "MYH6": "+"}},
    "TBX5": {"targets": {"MYH6": "+", "NKX2-5": "+"}},
    "ASCL1": {"targets": {"NEUROD1": "+", "MYT1L": "+", "OCT4": "-"}},
    "NEUROD1": {"targets": {"TUBB3": "+", "MAP2": "+"}},
    "MYT1L": {"targets": {"MAP2": "+", "SCN1A": "+"}},
    "MYOD1": {"targets": {"MYOG": "+", "MYH1": "+"}},
}
CELL_MARKERS = {
    "fibroblast": ["COL1A1", "VIM"], "neuron": ["TUBB3", "MAP2", "SCN1A"],
    "cardiomyocyte": ["TNNT2", "MYH6"], "ipsc": ["OCT4", "SOX2", "NANOG"],
    "muscle": ["MYOG", "MYH1"],
}


def lineage_network(focus: list[str] | None = None) -> dict:
    """Causal regulatory network with edge list and key regulatory nodes."""
    edges = []
    for src, d in LINEAGE_GRN.items():
        for dst, sign in d["targets"].items():
            if focus and src not in focus and dst not in focus:
                continue
            edges.append({"source": src, "target": dst,
                          "effect": "activates" if sign == "+" else "represses"})
    centrality: dict[str, int] = {}
    for e in edges:
        centrality[e["source"]] = centrality.get(e["source"], 0) + 1
    key_nodes = sorted(centrality, key=lambda k: -centrality[k])[:5]
    return {"nodes": sorted({e["source"] for e in edges} | {e["target"] for e in edges}),
            "edges": edges, "key_regulatory_nodes": key_nodes,
            "markers": CELL_MARKERS}


def transition_recipe(source: str, target: str) -> dict:
    """Stepwise genetic recipe: which nodes to push/pull and in what order."""
    net = lineage_network()
    target_markers = CELL_MARKERS.get(target.lower(), [])
    source_markers = CELL_MARKERS.get(source.lower(), [])
    drivers = [n for n, d in LINEAGE_GRN.items()
               if any(t in target_markers for t in d["targets"])]
    repressors = [n for n, d in LINEAGE_GRN.items()
                  if any(t in source_markers for t in d["targets"])]
    steps = []
    if drivers:
        steps.append({"order": 1, "action": "overexpress",
                      "nodes": sorted(set(drivers)),
                      "rationale": "activate target-lineage marker program"})
    if repressors:
        steps.append({"order": 2, "action": "repress/knockdown",
                      "nodes": sorted(set(repressors)),
                      "rationale": "silence source-lineage identity"})
    steps.append({"order": 3, "action": "select",
                  "nodes": target_markers,
                  "rationale": "enrich converted cells by marker expression"})
    return {
        "source": source, "target": target,
        "network": net,
        "recipe": steps,
        "expected_transition": f"{source} -> {target} via {len(drivers)} driver nodes",
    }
