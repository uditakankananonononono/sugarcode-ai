from __future__ import annotations

# Curated reprogramming knowledge (published protocols)
REPROGRAMMING_MAP = {
    ("fibroblast", "neuron"): {
        "tfs": ["ASCL1", "BRN2", "MYT1L"], "weeks": 3,
        "success_rate": 0.35, "reference": "Vierbuchen 2010"},
    ("fibroblast", "cardiomyocyte"): {
        "tfs": ["GATA4", "MEF2C", "TBX5"], "weeks": 4,
        "success_rate": 0.20, "reference": "Ieda 2010"},
    ("fibroblast", "hepatocyte"): {
        "tfs": ["HNF4A", "FOXA2", "HNF1A"], "weeks": 3,
        "success_rate": 0.25, "reference": "Huang 2011"},
    ("fibroblast", "ipsc"): {
        "tfs": ["OCT4", "SOX2", "KLF4", "MYC"], "weeks": 4,
        "success_rate": 0.01, "reference": "Takahashi-Yamanaka 2006"},
    ("b_cell", "macrophage"): {
        "tfs": ["CEBPA"], "weeks": 1,
        "success_rate": 0.80, "reference": "Xie 2004"},
    ("fibroblast", "endothelial"): {
        "tfs": ["ETV2", "FLI1", "ERG"], "weeks": 2,
        "success_rate": 0.30, "reference": "Morita 2015"},
}


def predict_reprogramming(source: str, target: str, delivery: str = "lentivirus") -> dict:
    """Predict TFs, protocol and success rate for a cell-fate conversion."""
    key = (source.lower(), target.lower())
    if key in REPROGRAMMING_MAP:
        r = REPROGRAMMING_MAP[key]
        known = True
    else:
        r = _infer(key)
        known = False
    delivery_factor = {"lentivirus": 1.0, "mRNA": 0.8, "episomal": 0.6,
                       "small_molecule": 0.5}.get(delivery, 0.7)
    rate = round(r["success_rate"] * delivery_factor, 3)
    return {
        "source": source, "target": target, "curated": known,
        "transcription_factors": r["tfs"],
        "estimated_success_rate": rate,
        "delivery": delivery,
        "protocol": _protocol(source, target, r["tfs"], r["weeks"], delivery),
        "duration_weeks": r["weeks"],
        "reference": r.get("reference", "inferred from lineage TF maps"),
        "validation": ["qPCR of source-marker silencing by week 1",
                       "immunostain for target markers at endpoint",
                       "functional assay (e.g. patch clamp for neurons)"],
    }


def _infer(key: tuple[str, str]) -> dict:
    core = {"neuron": ["ASCL1", "NEUROD1"], "cardiomyocyte": ["GATA4", "TBX5"],
            "hepatocyte": ["HNF4A", "FOXA2"], "beta_cell": ["PDX1", "NKX6.1"],
            "muscle": ["MYOD1"], "ipsc": ["OCT4", "SOX2", "KLF4", "MYC"]}
    tfs = core.get(key[1], ["OCT4", "SOX2"])
    return {"tfs": tfs, "weeks": 4, "success_rate": 0.05}


def _protocol(source: str, target: str, tfs: list[str], weeks: int, delivery: str) -> list[str]:
    return [
        f"culture {source} to 70% confluence",
        f"deliver {', '.join(tfs)} via {delivery} (MOI titrated)",
        "day 2: switch to induction media + small molecules as mapped",
        f"weeks 1-{weeks}: media changes every 2 days, monitor morphology",
        f"week {weeks}: score conversion by marker panel + function",
    ]
