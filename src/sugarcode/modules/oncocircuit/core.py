from __future__ import annotations

from ..synbio_studio.core import Circuit, Gate, simulate


TUMOR_PROMOTERS = {
    "hTERT": {"cancers": ["pan-cancer"], "tumor_selectivity": 0.85},
    "Survivin": {"cancers": ["lung", "breast", "colorectal"], "tumor_selectivity": 0.80},
    "AFP": {"cancers": ["hepatocellular"], "tumor_selectivity": 0.90},
    "PSA": {"cancers": ["prostate"], "tumor_selectivity": 0.92},
    "HER2_inducible": {"cancers": ["breast", "gastric"], "tumor_selectivity": 0.80},
}

PAYLOADS = {
    "caspase3": "direct apoptosis",
    "dtA": "diphtheria toxin A chain",
    "HSV-TK": "suicide gene (ganciclovir-activated)",
    "IL-12": "immune recruitment",
}


def _select_promoters(cancer_type: str) -> tuple[str, str]:
    cancer = cancer_type.casefold()
    candidates = [
        name
        for name, annotation in TUMOR_PROMOTERS.items()
        if cancer in {item.casefold() for item in annotation["cancers"]}
    ]
    primary = max(
        candidates or ["hTERT"],
        key=lambda name: TUMOR_PROMOTERS[name]["tumor_selectivity"],
    )
    secondary = "Survivin" if primary != "Survivin" else "hTERT"
    return primary, secondary


def design_oncocircuit(
    cancer_type: str,
    payload: str = "caspase3",
    two_input: bool = True,
) -> dict:
    """Design and simulate a tumor-selective therapeutic gene circuit.

    In dual-input mode, both a cancer-associated promoter and an independent
    proliferation-associated promoter must be active before the payload is
    expressed. Single-input mode is provided as a less selective comparator.
    """
    if not isinstance(cancer_type, str) or not cancer_type.strip():
        raise ValueError("cancer_type must be a non-empty string")
    if payload not in PAYLOADS:
        choices = ", ".join(sorted(PAYLOADS))
        raise ValueError(f"unknown payload {payload!r}; choose one of: {choices}")

    primary, secondary = _select_promoters(cancer_type.strip())
    promoter_names = [primary, secondary] if two_input else [primary]
    inputs = [(name, "activate") for name in promoter_names]
    logic = "AND" if two_input else "OR"
    circuit = Circuit(
        name=f"onco_{'_AND_'.join(promoter_names)}",
        gates=[Gate("killer", inputs, logic=logic, vmax=2.0)],
    )

    environments = {
        "tumor": {name: 3.0 for name in promoter_names},
        "normal": {name: (0.02 if index == 0 else 0.05) for index, name in enumerate(promoter_names)},
        "single_positive": {
            name: (3.0 if index == 0 else 0.05) for index, name in enumerate(promoter_names)
        },
    }
    outputs = {}
    for label, external in environments.items():
        result = simulate(circuit, (0, 200), external=external, n_points=40)
        outputs[label] = result["steady_state"]["killer"]

    tumor_output = max(outputs["tumor"], 1e-6)
    selectivity = round(outputs["tumor"] / max(outputs["normal"], 1e-6), 1)
    leakage = round(outputs["single_positive"] / tumor_output, 3)
    promoter_annotations = [
        {"name": name, **TUMOR_PROMOTERS[name]} for name in promoter_names
    ]
    promoter_text = " and ".join(promoter_names)
    gate_text = "co-active" if two_input else "active"

    return {
        "cancer_type": cancer_type,
        "promoters": promoter_names,
        "promoter_annotations": promoter_annotations,
        "logic": "AND (dual-input)" if two_input else "single-input",
        "payload": payload,
        "payload_action": PAYLOADS[payload],
        "circuit": {
            "name": circuit.name,
            "gates": [
                {"name": gate.name, "inputs": gate.inputs, "logic": gate.logic}
                for gate in circuit.gates
            ],
        },
        "simulation": {
            "output_tumor": outputs["tumor"],
            "output_normal": outputs["normal"],
            "output_single_positive": outputs["single_positive"],
        },
        "tumor_selectivity_fold": selectivity,
        "leakage_fraction": leakage,
        "molecular_mechanism": (
            f"{promoter_text} promoter activity is {gate_text} in the modeled malignant "
            f"cell; the gate drives {payload} ({PAYLOADS[payload]}). "
            + (
                "Cells with only one active input remain below the therapeutic output threshold."
                if two_input
                else "This comparator lacks the second-input safety constraint."
            )
        ),
        "delivery": "tumor-targeted AAV or LNP; see CRISPR Cargo",
        "model_status": (
            "ODE design simulation only; promoter activity, off-target expression, delivery, "
            "efficacy, and safety require experimental validation"
        ),
    }
