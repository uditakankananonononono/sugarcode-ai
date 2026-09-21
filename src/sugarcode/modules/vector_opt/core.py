from __future__ import annotations
import random

CAPSID_REGIONS = {
    "VR-IV": {"surface": True, "nab_epitope": True, "receptor_contact": True},
    "VR-VIII": {"surface": True, "nab_epitope": True, "receptor_contact": False},
    "GH_loop": {"surface": True, "nab_epitope": True, "receptor_contact": True},
    "HI_loop": {"surface": True, "nab_epitope": False, "receptor_contact": False},
    "threefold_spike": {"surface": True, "nab_epitope": False, "receptor_contact": True},
}
CONSERVATION = {"VR-IV": 0.3, "VR-VIII": 0.4, "GH_loop": 0.35,
                "HI_loop": 0.7, "threefold_spike": 0.5}


def engineer_capsid(capsid: str = "AAV9", target_receptor: str = "generic",
                    nab_escape: bool = True, n_variants: int = 6,
                    seed: int = 1) -> dict:
    """Design capsid variants trading receptor affinity vs NAb escape.

    Mutations scored: receptor-contact gain (if receptor region), NAb epitope
    disruption, conservation penalty (structural integrity).
    """
    rng = random.Random(seed)
    variants = []
    for i in range(n_variants):
        region = rng.choice(list(CAPSID_REGIONS))
        props = CAPSID_REGIONS[region]
        n_mut = rng.randint(1, 4)
        receptor_gain = (0.15 * n_mut * (1 if props["receptor_contact"] else 0.2)
                         * rng.uniform(0.7, 1.3))
        nab_loss = (0.2 * n_mut if props["nab_epitope"] else 0.02 * n_mut) * rng.uniform(0.7, 1.3)
        integrity = 1.0 - 0.08 * n_mut * (1 - CONSERVATION[region])
        transduction = 0.5 + receptor_gain - (1 - integrity)
        variants.append({
            "variant_id": f"{capsid}-V{i + 1}", "region": region,
            "n_mutations": n_mut,
            "receptor_affinity_gain": round(receptor_gain, 3),
            "nab_escape_score": round(min(nab_loss, 1.0), 3),
            "capsid_integrity": round(integrity, 3),
            "predicted_transduction": round(max(0.0, min(1.0, transduction)), 3),
        })
    if nab_escape:
        variants.sort(key=lambda v: -(v["nab_escape_score"] * 0.5 + v["predicted_transduction"] * 0.5))
    else:
        variants.sort(key=lambda v: -v["predicted_transduction"])
    best = variants[0]
    return {
        "parent_capsid": capsid, "target_receptor": target_receptor,
        "variants": variants, "lead": best,
        "docking_summary": {
            "model": "capsid-receptor interface scoring on variable-region contacts",
            "lead_receptor_gain": best["receptor_affinity_gain"],
        },
        "nab_panel_prediction": {
            "sera_escape_fraction": round(best["nab_escape_score"] * 0.8, 3),
            "note": "predicted against common NAb epitopes; validate with patient sera panel",
        },
        "next_steps": ["synthesize lead + 2 alternates", "transduction assay in target cells",
                       "NAb neutralization assay", "in vivo biodistribution"],
    }
