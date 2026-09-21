from __future__ import annotations

# Curated rare-disease HPO-style signatures
RARE_DISEASES = {
    "cystic_fibrosis": {"symptoms": {"chronic_cough", "salty_skin", "poor_growth", "recurrent_lung_infection"},
                        "genes": ["CFTR"], "prevalence": 0.0001},
    "huntingtons": {"symptoms": {"chorea", "cognitive_decline", "mood_changes", "adult_onset"},
                    "genes": ["HTT"], "prevalence": 0.00005},
    "marfan": {"symptoms": {"tall_stature", "aortic_dilation", "lens_dislocation", "long_limbs"},
               "genes": ["FBN1"], "prevalence": 0.0001},
    "phenylketonuria": {"symptoms": {"intellectual_disability", "musty_odor", "eczema", "seizures"},
                        "genes": ["PAH"], "prevalence": 0.00008},
    "gaucher": {"symptoms": {"hepatosplenomegaly", "bone_pain", "anemia", "fatigue"},
                "genes": ["GBA"], "prevalence": 0.00006},
    "duchenne_md": {"symptoms": {"muscle_weakness", "gower_sign", "calf_hypertrophy", "childhood_onset"},
                    "genes": ["DMD"], "prevalence": 0.0001},
}


def diagnose(symptoms: list[str], variants: list[dict] | None = None,
             omics: dict | None = None) -> dict:
    """Correlate symptoms with genomic/multi-omic evidence into ranked candidates.

    Score = symptom overlap (weighted by symptom specificity) + variant support
    + omics corroboration; explainable per-candidate evidence chain.
    """
    sym = {s.lower() for s in symptoms}
    variant_genes = {v.get("gene", "").upper() for v in (variants or [])}
    omics = omics or {}
    cands = []
    for disease, d in RARE_DISEASES.items():
        overlap = sym & d["symptoms"]
        if not overlap:
            continue
        specificity = sum(1 / max(1, _symptom_frequency(s)) for s in overlap)
        sym_score = min(1.0, 0.25 * len(overlap) + 0.1 * specificity)
        var_score = 0.4 if set(d["genes"]) & variant_genes else 0.0
        om_score = 0.15 if any(g in omics.get("disrupted_genes", []) for g in d["genes"]) else 0.0
        conf = round(min(0.99, sym_score + var_score + om_score), 3)
        evidence = [{"type": "symptom_match", "detail": sorted(overlap)},
                    *([{"type": "variant", "detail": sorted(set(d["genes"]) & variant_genes)}] if var_score else []),
                    *([{"type": "omics", "detail": "gene disrupted in supplied omics"}] if om_score else [])]
        cands.append({"disease": disease, "confidence": conf,
                      "genes": d["genes"], "evidence": evidence,
                      "explainable": True})
    cands.sort(key=lambda c: -c["confidence"])
    return {
        "symptoms_input": sorted(sym),
        "candidates": cands,
        "top": cands[0] if cands else None,
        "next_steps": _next_steps(cands[0]) if cands else ["broaden phenotyping (HPO terms)", "consider exome/genome sequencing"],
        "treatments": _treatments(cands[0]["disease"]) if cands else [],
        "disclaimer": "decision support for clinicians; not a standalone diagnosis",
    }


def _symptom_frequency(symptom: str) -> int:
    """How many catalog diseases share this symptom (specificity denominator)."""
    return sum(1 for d in RARE_DISEASES.values() if symptom in d["symptoms"])


def _next_steps(top: dict) -> list[str]:
    return [f"confirmatory genetic test: {', '.join(top['genes'])}",
            "specialist referral with this evidence summary",
            "family segregation analysis"]


def _treatments(disease: str) -> list[dict]:
    tx = {"cystic_fibrosis": [{"name": "CFTR modulators (ivacaftor/tezacaftor)", "type": "targeted"}],
          "gaucher": [{"name": "enzyme replacement (imiglucerase)", "type": "ERT"}],
          "phenylketonuria": [{"name": "low-phenylalanine diet + sapropterin", "type": "metabolic"}],
          "duchenne_md": [{"name": "exon-skipping (eteplirsen, mutation-dependent)", "type": "genetic"},
                          {"name": "corticosteroids", "type": "supportive"}]}
    return tx.get(disease, [{"name": "symptomatic management + clinical trial search", "type": "supportive"}])
