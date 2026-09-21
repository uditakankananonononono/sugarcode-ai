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


def enrich_variants_live(variants: list[dict], retmax: int = 10,
                         offline: bool = False) -> list[dict]:
    """Attach live ClinVar classifications to patient variants.

    For each variant with a gene symbol, queries ClinVar live and attaches the
    gene's current pathogenic/likely-pathogenic entries plus any title that
    matches the variant's own notation (e.g. c. / p. change). Sources named;
    failures reported, never hidden.
    """
    from ...bio import entrez
    out = []
    for v in variants:
        gene = (v.get("gene") or "").upper()
        ev = dict(v)
        if not gene:
            ev["clinvar"] = {"status": "no gene symbol - skipped"}
            out.append(ev)
            continue
        try:
            entries = entrez.clinvar_variants(gene, retmax=retmax, offline=offline)
            notation = v.get("hgvs") or v.get("change") or ""
            matched = [e for e in entries
                       if notation and notation.split(":")[-1] in e["title"]]
            path = [e for e in entries if "athogenic" in (e["significance"] or "")]
            ev["clinvar"] = {
                "status": "live",
                "gene_entries": len(entries),
                "pathogenic_or_likely": len(path),
                "exact_match": matched,
                "interpretation_hint": (
                    "this exact variant is classified " + matched[0]["significance"]
                    if matched else
                    f"gene has {len(path)} pathogenic/likely entries; this variant not matched - "
                    "VUS until classified"),
            }
        except Exception as e:
            ev["clinvar"] = {"status": f"lookup failed: {type(e).__name__}: {e}"}
        # gnomAD population frequency (drop 16): rarity is core rare-disease
        # evidence. Absence is a real answer; failures reported.
        vid = v.get("variant_id") or v.get("gnomad_id")
        if vid:
            try:
                from ...bio import gnomad
                f = gnomad.variant_frequency(vid, offline=offline)
                if f["present"]:
                    af = f.get("max_af") or 0.0
                    f["rarity_interpretation"] = (
                        "too common for a rare-disease cause (AF > 1%)" if af > 0.01
                        else "rare (AF < 1%) - compatible with rare-disease causality" if af > 0
                        else "present but zero AF reported")
                ev["gnomad"] = f
            except Exception as e:
                ev["gnomad"] = {"status": f"lookup failed: {type(e).__name__}: {e}"}
        else:
            ev["gnomad"] = {"status": "no GRCh38 variant_id - skipped"}
        out.append(ev)
    return out
