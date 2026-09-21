from __future__ import annotations
from ..synbio_studio.core import Circuit, Gate, simulate

TUMOR_PROMOTERS = {
    "hTERT": {"cancers": ["pan-cancer"], "tumor_selectivity": 0.85},
    "Survivin": {"cancers": ["lung", "breast", "colorectal"], "tumor_selectivity": 0.8},
    "AFP": {"cancers": ["hepatocellular"], "tumor_selectivity": 0.9},
    "PSA": {"cancers": ["prostate"], "tumor_selectivity": 0.92},
    "HER2_inducible": {"cancers": ["breast", "gastric"], "tumor_selectivity": 0.8},
}
PAYLOADS = {"caspase3": "direct apoptosis", "dtA": "diphtheria toxin A chain",
            "HSV-TK": "suicide gene (ganciclovir-activated)", "IL-12": "immune recruitment"}


def design_oncocircuit(cancer_type: str, payload: str = "caspase3",
                       two_input: bool = True) -> dict:
    """Logic-gated circuit that fires only in malignant cells.

    Two-promoter AND gate: promoter A (tumor-selective) + promoter B
    (generic proliferation marker) must both be active -> therapeutic output.
    """
    promoters = [p for p, v in TUMOR_PROMOTERS.items()
                 if cancer_type.lower() in [c.lower() for c in v["cancers"]]]
    if not promoters:
        promoters = ["hTERT"]  # pan-cancer fallback
    pa = promoters[0]
    pb = "Survivin" if pa != "Survivin" else "hTERT"
    circuit = Circuit(name=f"onco_{pa}_AND_{pb}", gates=[
        Gate("killer", [(pa, "activate"), (pb, "activate")], logic="AND", vmax=2.0),
    ])
    # simulate: tumor cell (both on), normal cell (both off), adjacent (one on)
    sims = {}
    for label, ext in {"tumor": {pa: 3.0, pb: 3.0}, "normal": {pa: 0.02, pb: 0.05},
                       "single_positive": {pa: 3.0, pb: 0.05}}.items():
        r = simulate(circuit, (0, 200), external=ext, n_points=40)
        sims[label] = r["steady_state"]["killer"]
    selectivity = round(sims["tumor"] / max(sims["normal"], 1e-6), 1)
    leak = round(sims["single_positive"] / max(sims["tumor"], 1e-6), 3)
    return {
        "cancer_type": cancer_type,
        "promoters": [pa, pb] if two_input else [pa],
        "logic": "AND (dual-input)" if two_input else "single-input",
        "payload": payload, "payload_action": PAYLOADS[payload],
        "circuit": {"gates": [{"name": g.name, "inputs": g.inputs, "logic": g.logic}
                              for g in circuit.gates]},
        "simulation": {"output_tumor": sims["tumor"], "output_normal": sims["normal"],
                       "output_single_positive": sims["single_positive"]},
        "tumor_selectivity_fold": selectivity,
        "leakage_fraction": leak,
        "molecular_mechanism": (f"{pa} and {pb} promoters co-active only in malignant cells; "
                                f"AND gate drives {payload} ({PAYLOADS[payload]}) - "
                                "normal tissue sees at most one input and stays silent"),
        "delivery": "tumor-targeted AAV or LNP; see CRISPR Cargo",
    }
