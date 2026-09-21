from __future__ import annotations

DRIFT_RATES = {"mutation_retention": 0.98, "expression_drift": 0.05,
               "stroma_replacement": 0.15, "subclone_selection": 0.08}


def fidelity_assessment(patient_profile: dict, pdx_profile: dict,
                        passage: int = 3) -> dict:
    """Model Fidelity Index: how well the PDX still represents the patient.

    Compares mutation retention, expression correlation and stroma state;
    flags translational drift and proposes CRISPR restoration when needed.
    """
    p_mut = set(patient_profile.get("mutations", []))
    x_mut = set(pdx_profile.get("mutations", []))
    retention = len(p_mut & x_mut) / max(1, len(p_mut)) if p_mut else 1.0
    retention_adj = retention * (DRIFT_RATES["mutation_retention"] ** passage)
    p_expr = patient_profile.get("expression", {})
    x_expr = pdx_profile.get("expression", {})
    corr = _correlation(p_expr, x_expr)
    corr_adj = corr * (1 - DRIFT_RATES["expression_drift"]) ** passage
    stroma = min(1.0, DRIFT_RATES["stroma_replacement"] * passage)
    subclone = min(1.0, DRIFT_RATES["subclone_selection"] * passage)
    mfi = round(0.4 * retention_adj + 0.35 * corr_adj
                + 0.15 * (1 - stroma) + 0.10 * (1 - subclone), 3)
    drift_flags = []
    if retention_adj < 0.8:
        drift_flags.append("key driver mutations lost in PDX")
    if corr_adj < 0.7:
        drift_flags.append("expression program drifting from patient")
    if stroma > 0.4:
        drift_flags.append("human stroma largely replaced by mouse")
    restoration = _restoration(p_mut - x_mut) if p_mut - x_mut else None
    return {
        "passage": passage,
        "model_fidelity_index": mfi,
        "components": {"mutation_retention": round(retention_adj, 3),
                       "expression_correlation": round(corr_adj, 3),
                       "stroma_human_fraction": round(1 - stroma, 3),
                       "subclone_drift": round(subclone, 3)},
        "translational_drift": drift_flags,
        "verdict": ("high fidelity - results translate" if mfi > 0.8 else
                    "moderate - interpret with caution" if mfi > 0.6 else
                    "low fidelity - re-derive model from patient sample"),
        "crispr_restoration": restoration,
    }


def _correlation(a: dict, b: dict) -> float:
    genes = set(a) & set(b)
    if len(genes) < 2:
        return 0.5
    import math
    xa = [a[g] for g in genes]
    xb = [b[g] for g in genes]
    ma, mb = sum(xa) / len(xa), sum(xb) / len(xb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(xa, xb))
    va = math.sqrt(sum((x - ma) ** 2 for x in xa))
    vb = math.sqrt(sum((y - mb) ** 2 for y in xb))
    return cov / (va * vb) if va and vb else 0.5


def _restoration(lost: set) -> dict:
    return {"strategy": "CRISPR knock-in of lost driver mutations into PDX cells",
            "targets": sorted(lost),
            "method": "see CRISPR Opt for guide design",
            "note": "restores patient-relevant genotype before further passaging"}
