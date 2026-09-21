from __future__ import annotations
import math


def create_twin(patient_omics: dict) -> dict:
    """Build a digital cell state from multi-omic measurements.

    patient_omics: {"mutations": [...], "expression": {gene: tpm},
                    "proteomics": {protein: abundance}, "metadata": {...}}
    The twin is a parameterized state vector driving response models.
    """
    mutations = patient_omics.get("mutations", [])
    expression = patient_omics.get("expression", {})
    drivers = [m for m in mutations if m.get("driver_score", 0) > 0.5]
    state = {
        "proliferation_index": round(_proliferation(expression), 3),
        "apoptosis_threshold": round(_apoptosis_threshold(mutations), 3),
        "driver_mutations": drivers,
        "expression_signature": dict(sorted(expression.items(),
                                            key=lambda kv: -kv[1])[:20]),
        "metadata": patient_omics.get("metadata", {}),
    }
    state["twin_id"] = f"twin-{abs(hash(str(sorted(expression.items()))) % 10**6)}"
    return state


def _proliferation(expr: dict) -> float:
    markers = {"MKI67": 0.4, "PCNA": 0.3, "CCND1": 0.2, "MYC": 0.1}
    total = sum(expr.get(g, 0) * w for g, w in markers.items())
    return min(1.0, total / 200.0)


def _apoptosis_threshold(muts: list[dict]) -> float:
    base = 0.5
    for m in muts:
        gene = m.get("gene", "")
        if gene == "TP53":
            base += 0.3
        elif gene in ("BCL2", "MCL1"):
            base += 0.2
        elif gene in ("BAX", "BAK1"):
            base -= 0.15
    return min(0.95, max(0.05, base))


DRUG_ACTIONS = {
    "cisplatin": {"target": "DNA crosslinks", "kill": 0.7, "resist_genes": ["ERCC1", "TP53"]},
    "trametinib": {"target": "MEK inhibitor", "kill": 0.6, "resist_genes": ["KRAS", "BRAF_amp"]},
    "olaparib": {"target": "PARP inhibitor", "kill": 0.75, "resist_genes": ["BRCA1_rev", "TP53BP1_loss"]},
    "venetoclax": {"target": "BCL2 inhibitor", "kill": 0.65, "resist_genes": ["MCL1", "BCLXL"]},
    "gefitinib": {"target": "EGFR inhibitor", "kill": 0.6, "resist_genes": ["EGFR_T790M", "MET_amp"]},
}


def run_drug_trial(twin: dict, drugs: list[str], doses: list[float] | None = None) -> dict:
    """In silico trial: per-drug and combination response on the twin.

    Response = kill efficacy adjusted by driver resistance and apoptosis
    threshold; Bliss independence for combinations.
    """
    doses = doses or [0.1, 1.0, 10.0]
    driver_genes = {m.get("gene") for m in twin.get("driver_mutations", [])}
    per_drug = {}
    for d in drugs:
        if d not in DRUG_ACTIONS:
            continue
        act = DRUG_ACTIONS[d]
        resist = 0.5 if driver_genes & set(act["resist_genes"]) else 0.0
        curves = []
        for dose in doses:
            eff = act["kill"] * (dose / (dose + 1.0)) * (1 - resist)
            apoptosis = eff * (1 - twin["apoptosis_threshold"])
            proliferation = twin["proliferation_index"] * (1 - eff)
            curves.append({"dose_uM": dose, "apoptosis_rate": round(apoptosis, 3),
                           "proliferation_rate": round(proliferation, 3)})
        per_drug[d] = {"curves": curves, "resistance_flag": bool(resist),
                       "max_apoptosis": curves[-1]["apoptosis_rate"]}
    combos = []
    for i in range(len(drugs)):
        for j in range(i + 1, len(drugs)):
            a, b = drugs[i], drugs[j]
            if a in per_drug and b in per_drug:
                ea = per_drug[a]["max_apoptosis"]
                eb = per_drug[b]["max_apoptosis"]
                bliss = ea + eb - ea * eb
                combos.append({"combination": [a, b],
                               "predicted_apoptosis": round(bliss, 3),
                               "synergy_model": "Bliss independence"})
    combos.sort(key=lambda c: -c["predicted_apoptosis"])
    ranked = sorted(per_drug.items(), key=lambda kv: -kv[1]["max_apoptosis"])
    return {
        "twin_id": twin.get("twin_id"),
        "per_drug": per_drug,
        "combinations": combos,
        "recommended": combos[0] if combos else (
            {"monotherapy": ranked[0][0]} if ranked else None),
    }
