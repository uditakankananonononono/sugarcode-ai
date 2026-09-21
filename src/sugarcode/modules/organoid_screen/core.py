from __future__ import annotations
from ..organoid_ai.core import drug_response


def screen(tissue: str, compounds: list[str], mutations: list[str] | None = None) -> dict:
    """Screen a compound library on an organoid model; rank + synergy + biomarkers."""
    resp = drug_response(tissue, compounds, mutations)
    ranked = sorted(resp["responses"].items(), key=lambda kv: kv[1]["ic50_uM"])
    synergies = _synergy(resp["responses"])
    biomarkers = _biomarkers(mutations or [], ranked)
    return {
        "tissue": tissue, "mutations": mutations or [],
        "screened": len(compounds),
        "ranking": [{"compound": c, "ic50_uM": d["ic50_uM"]} for c, d in ranked],
        "hit": ranked[0][0] if ranked else None,
        "synergy": synergies,
        "response_biomarkers": biomarkers,
        "interaction_network": _network(mutations or [], [c for c, _ in ranked[:3]]),
        "clinical_efficacy_prediction": round(0.4 + 0.3 * (1 / (1 + ranked[0][1]["ic50_uM"])), 3) if ranked else None,
    }


def _synergy(responses: dict) -> list[dict]:
    items = list(responses.items())
    out = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            (ca, da), (cb, db) = items[i], items[j]
            # Bliss-style combined index from IC50s
            ci = round(da["ic50_uM"] / (da["ic50_uM"] + db["ic50_uM"])
                       + db["ic50_uM"] / (da["ic50_uM"] + db["ic50_uM"]) - 1.0, 3)
            out.append({"combination": [ca, cb], "combination_index": abs(ci),
                        "synergy_score": round(1 - abs(ci), 3)})
    out.sort(key=lambda x: -x["synergy_score"])
    return out


def _biomarkers(mutations: list[str], ranked: list) -> list[dict]:
    known = {"BRCA1_rev": "PARP-inhibitor resistance", "TP53": "general resistance",
             "KRAS": "MEK/EGFR pathway dependence", "EGFR_T790M": "1st-gen EGFRi resistance"}
    return [{"marker": m, "interpretation": known.get(m, "uncharacterized"),
             "actionable": m in known} for m in mutations]


def _network(mutations: list[str], top: list[str]) -> dict:
    nodes = list(mutations) + list(top)
    edges = [{"from": m, "to": c, "kind": "sensitizes/resists"}
             for m in mutations for c in top]
    return {"nodes": nodes, "edges": edges}
