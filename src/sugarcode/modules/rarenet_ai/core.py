from __future__ import annotations

import re

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
    sym = {s.lower().replace(" ", "_") for s in symptoms}
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
            notation = v.get("hgvs") or v.get("change") or ""
            if notation:
                # exact phrase query + title verification (same discipline as
                # openclinvar): gene-page scans miss variants past the first page
                entries = entrez.clinvar_exact(gene, notation, offline=offline)
                needle = notation.split(":")[-1].replace(" ", "")
                # HGVS: ClinVar titles drop deleted/duplicated bases
                # (c.1521_1523delCTT -> c.1521_1523del). Normalize both sides.
                _norm = lambda s: re.sub(r"(del|dup|ins)[ACGT]+$", r"\1", s)
                nneedle = _norm(needle)
                matched = [e for e in entries if needle and (
                    needle in e["title"].replace(" ", "") or
                    (nneedle != needle and nneedle in _norm(e["title"].replace(" ", ""))))]
            else:
                entries = entrez.clinvar_variants(gene, retmax=retmax, offline=offline)
                matched = []
            path = [e for e in entries if "athogenic" in (e["significance"] or "")]
            ev["clinvar"] = {
                "status": "live",
                "query": ("exact" if notation else "gene-page"),
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


# --- drop 19: combined variant evidence panel (diagnostic-workflow capstone) ---
def variant_evidence_panel(variants: list[dict], offline: bool = False) -> dict:
    """One panel per patient variant: live ClinVar classification, gnomAD
    population frequency + rarity, and gene constraint (pLI/LOEUF) - combined
    into a named-component support score. This aggregates evidence for a
    clinician; it does NOT diagnose. Every component names its source; every
    failure is reported, none hidden."""
    from ...bio import gnomad
    enriched = enrich_variants_live(variants, offline=offline)
    constraint_cache: dict[str, dict] = {}
    panel = []
    for ev in enriched:
        gene = (ev.get("gene") or "").upper()
        if gene and gene not in constraint_cache:
            try:
                constraint_cache[gene] = gnomad.gene_constraint(gene, offline=offline)
            except Exception as e:
                constraint_cache[gene] = {"status": f"lookup failed: {type(e).__name__}: {e}"}
        c = constraint_cache.get(gene, {})
        components = []
        score = 0.0
        cl = ev.get("clinvar", {})
        if cl.get("exact_match"):
            from ..openclinvar.core import clinvar_stars, STAR_WEIGHT
            m0 = cl["exact_match"][0]
            sig = (m0["significance"] or "").lower()
            stars = clinvar_stars(m0.get("review_status"))
            # base 2.0 is calibrated on 3-star (expert panel, weight 0.8);
            # other tiers scale proportionally (drop 25)
            w = round(2.0 * STAR_WEIGHT[stars] / 0.8, 2)
            if "pathogenic" in sig and "benign" not in sig and "conflicting" not in sig:
                score += w
                components.append(f"ClinVar pathogenic, {stars}-star review (+{w})")
            elif "benign" in sig:
                score -= w
                components.append(f"ClinVar benign, {stars}-star review (-{w})")
            else:
                components.append("ClinVar entry conflicting/uncertain (0)")
        g = ev.get("gnomad", {})
        if g.get("present") is False:
            score += 0.5
            components.append("absent from gnomAD - consistent with rare (+0.5)")
        elif g.get("present") and (g.get("max_af") or 0) > 0.01:
            score -= 1.5
            components.append(f"common in population (AF {g['max_af']:.3g}) (-1.5)")
        elif g.get("present"):
            score += 0.25
            components.append(f"rare in population (AF {g.get('max_af', 0):.3g}) (+0.25)")
        # splice evidence (drop 25): natural-site delta on the gene's real
        # RefSeqGene junction map; deep-intronic -> cryptic_scan. Weak
        # perturbations are NOT evidence (BRCA1-validated) and add nothing.
        hgvs = ev.get("hgvs") or ev.get("change") or ""
        import re as _re
        if gene and _re.fullmatch(r"(?:[A-Z0-9_\.]+\()?c\.(?:-?\d+|\*\d+)[+-]\d+[ACGT]>[ACGT]\)?",
                                  hgvs.replace(" ", "")) or _re.fullmatch(
                                  r"c\.-?\d+[+-]\d+[ACGT]>[ACGT]", hgvs.replace(" ", "")):
            try:
                from ..deepsplice import live_splice_assessment
                sa = live_splice_assessment(gene, hgvs.split(":")[-1].split("(")[-1].rstrip(")"),
                                            offline=offline)
                # drop 30: carry the U12 flags and exon-skip context through
                # to the panel, and surface them in the readable components.
                ev["splice_assessment"] = {k: v for k, v in sa.items()
                                           if k in ("status", "site_type", "site_class",
                                                    "delta", "consequence", "verdict",
                                                    "source", "strong_findings",
                                                    "exon_context", "donor_subtype",
                                                    "u12_atac", "u12_note")}
                if sa.get("status") == "natural_site":
                    d = sa["delta"]
                    u12 = (f" [{sa['donor_subtype']}]" if sa.get("donor_subtype")
                           else " [AT-AC U12]" if sa.get("u12_atac") else "")
                    if d <= -0.15:
                        score += 1.5
                        esc = sa.get("exon_context") or {}
                        frame = ""
                        if esc:
                            frame = (f"; exon-skip context: {esc['skipped_exon']['length']} nt "
                                     f"{'in-frame' if esc['in_frame'] else 'out-of-frame'}")
                        # drop 36: surface retention + cryptic-use outcomes
                        alt = (esc.get("alternative_outcomes") or {}) if esc else {}
                        if alt.get("intron_retention"):
                            frame += f"; {alt['intron_retention'].split(':')[0]}"
                        cu = (alt.get("cryptic_use") or {}).get("candidates") or []
                        if cu:
                            frame += (f"; cryptic {sa['site_type']} candidate at "
                                      f"{cu[0]['offset_nt']:+d} nt ({cu[0]['score']:.2f})")
                        components.append(f"predicted loss of natural {sa['site_type']} "
                                          f"site{u12} (delta {d:+.2f}, RefSeqGene map{frame}) (+1.5)")
                    elif d <= -0.05:
                        score += 0.5
                        components.append(f"weakened {sa['site_type']} site (delta {d:+.2f}) (+0.5)")
                    else:
                        components.append(f"minimal splice-site effect (delta {d:+.2f}) (0)")
                elif sa.get("status") == "cryptic_scan" and sa.get("strong_findings"):
                    score += 1.0
                    f0 = sa["strong_findings"][0]
                    components.append(f"NEW cryptic {f0['site_type']} site "
                                      f"({f0['ref_score']:.2f}->{f0['alt_score']:.2f}) (+1.0)")
                elif sa.get("status") == "cryptic_scan":
                    components.append("no strong cryptic-site signal (0)")
            except Exception as e:
                ev["splice_assessment"] = {"status": f"assessment failed: {type(e).__name__}: {e}"}
        LOF = {"frameshift", "nonsense", "stop_gained", "splice_acceptor", "splice_donor"}
        cons = ev.get("consequence", "")
        if c.get("lof_constrained") and cons in LOF:
            score += 0.5
            components.append(f"LOF consequence in constrained gene (LOEUF {c['loeuf']:.3g}) (+0.5)")
        panel.append({**ev, "gene_constraint": c,
                      "support_score": round(score, 2),
                      "score_components": components,
                      "evidence_class": ("strong support" if score >= 2.0 else
                                         "moderate support" if score >= 0.75 else
                                         "little/no support" if score >= -0.5 else "evidence against")})
    panel.sort(key=lambda p: -p["support_score"])
    return {
        "panel": panel,
        "n_variants": len(panel),
        "scoring": {"clinvar_pathogenic_3star": 2.0, "clinvar_benign_3star": -2.0,
                    "clinvar_star_scaling": "x STAR_WEIGHT/0.8 (4-star 2.5, 2-star 1.5, 1-star 0.75, 0-star 0.38)",
                    "splice_natural_site_loss": 1.5, "splice_site_weakened": 0.5,
                    "splice_new_cryptic_site": 1.0,
                    "gnomad_absent": 0.5, "gnomad_common_af>1%": -1.5,
                    "gnomad_rare": 0.25, "lof_in_constrained_gene": 0.5},
        "disclaimer": ("evidence aggregation only - component weights are ours, "
                       "sources named per component; a clinician adjudicates. "
                       "Not a diagnosis."),
    }

# --- specification-complete explainable diagnostic reasoning -----------------
def normalize_phenotypes(symptoms: list[str]) -> dict:
    """Normalize clinician-entered phenotypes and report unknown terms explicitly."""
    if not isinstance(symptoms,list) or not symptoms: raise ValueError("symptoms must be a non-empty list of strings")
    if any(not isinstance(s,str) or not s.strip() for s in symptoms): raise ValueError("each symptom must be non-empty text")
    aliases={"cough":"chronic_cough","failure_to_thrive":"poor_growth","enlarged_spleen":"hepatosplenomegaly",
             "weakness":"muscle_weakness","gowers_sign":"gower_sign","fits":"seizures","ectopia_lentis":"lens_dislocation"}
    catalog=set().union(*(d["symptoms"] for d in RARE_DISEASES.values())); normalized=[]
    for raw in symptoms:
        term=raw.lower().strip().replace("-","_").replace(" ","_"); normalized.append(aliases.get(term,term))
    return {"normalized":sorted(set(normalized)),"recognized":sorted(set(normalized)&catalog),
            "unrecognized":sorted(set(normalized)-catalog),"coverage":len(set(normalized)&catalog)/len(set(normalized))}


def explainable_rank(symptoms: list[str], variants: list[dict] | None=None, omics: dict | None=None,
                     inheritance: str | None=None, negative_symptoms: list[str] | None=None) -> dict:
    """Rank diseases with Bayesian log-odds and a per-evidence contribution ledger."""
    import math
    norm=normalize_phenotypes(symptoms); present=set(norm["normalized"]); absent=set(normalize_phenotypes(negative_symptoms)["normalized"]) if negative_symptoms else set()
    variants=list(variants or []); omics=dict(omics or {}); allowed={None,"dominant","recessive","x_linked"}
    if inheritance not in allowed: raise ValueError("inheritance must be dominant, recessive, x_linked, or None")
    rows=[]
    for disease,d in RARE_DISEASES.items():
        ledger=[]; prior=min(max(d["prevalence"],1e-9),1-1e-9); logodds=math.log(prior/(1-prior))
        for s in sorted(present):
            if s in d["symptoms"]: contribution=math.log(8/max(_symptom_frequency(s),1)); ledger.append({"evidence":"phenotype_present","item":s,"log_likelihood":contribution}); logodds+=contribution
        for s in sorted(absent & d["symptoms"]): ledger.append({"evidence":"phenotype_absent","item":s,"log_likelihood":-math.log(4)}); logodds-=math.log(4)
        for v in variants:
            if str(v.get("gene","")).upper() in d["genes"]:
                pathogenic=str(v.get("classification","")).lower() in {"pathogenic","likely_pathogenic"}
                rarity=1-float(v.get("allele_frequency",0)); c=(math.log(30) if pathogenic else math.log(5))*max(.1,rarity)
                ledger.append({"evidence":"genomic_variant","item":v.get("id",v.get("hgvs",v["gene"])),"log_likelihood":c}); logodds+=c
        disrupted={str(g).upper() for g in omics.get("disrupted_genes",[])}
        if disrupted & set(d["genes"]): ledger.append({"evidence":"multi_omic","item":sorted(disrupted&set(d["genes"])),"log_likelihood":math.log(4)}); logodds+=math.log(4)
        posterior=1/(1+math.exp(-max(-40,min(40,logodds))))
        rows.append({"disease":disease,"genes":d["genes"],"posterior":round(posterior,9),"log_odds":round(logodds,6),"evidence_ledger":ledger,
                     "matched_phenotypes":sorted(present&d["symptoms"]),"contradicted_phenotypes":sorted(absent&d["symptoms"])})
    rows.sort(key=lambda x:(-x["posterior"],x["disease"]))
    return {"candidates":rows,"top":rows[0],"phenotype_normalization":norm,"inheritance_assumption":inheritance,
            "model_status":"mechanistic hermetic Bayesian evidence model; no trained or clinical claims"}


def diagnostic_workup(symptoms: list[str], variants: list[dict] | None=None, omics: dict | None=None,
                      *, inheritance: str | None=None, negative_symptoms: list[str] | None=None) -> dict:
    """Produce an actionable, review-ready rare-disease workup for a clinical scientist."""
    ranked=explainable_rank(symptoms,variants,omics,inheritance,negative_symptoms); top=ranked["top"]
    return {"ranking":ranked,"candidate_diseases":ranked["candidates"],"associated_genes":sorted(set(sum((x["genes"] for x in ranked["candidates"][:3]),[]))),
            "confirmatory_plan":[f"orthogonally confirm variants in {', '.join(top['genes'])}","complete three-generation pedigree","review phenotype ontology with a genetics specialist","consider reanalysis when knowledge changes"],
            "treatment_insights":_treatments(top["disease"]),"urgent_findings":[],
            "model_status":"mechanistic hermetic decision support; clinician adjudication required"}


def enhancement_features(symptoms: list[str], variants: list[dict] | None=None, omics: dict | None=None,
                         negative_symptoms: list[str] | None=None) -> dict:
    """Compute exactly 54 independently meaningful workflow diagnostics."""
    variants=list(variants or []); omics=dict(omics or {}); rank=explainable_rank(symptoms,variants,omics,negative_symptoms=negative_symptoms); norm=rank["phenotype_normalization"]
    c=rank["candidates"]; top=c[0]; present=set(norm["normalized"]); neg=set(normalize_phenotypes(negative_symptoms)["normalized"]) if negative_symptoms else set()
    genes={str(v.get("gene","")).upper() for v in variants if v.get("gene")}; af=[float(v.get("allele_frequency",0)) for v in variants]
    classifications=[str(v.get("classification","")).lower() for v in variants]
    out={
    "phenotype_input_count":len(symptoms),"phenotype_unique_count":len(present),"phenotype_recognized_count":len(norm["recognized"]),"phenotype_unknown_count":len(norm["unrecognized"]),
    "phenotype_catalog_coverage":norm["coverage"],"negative_phenotype_count":len(neg),"candidate_count":len(c),"top_disease":top["disease"],"top_posterior":top["posterior"],
    "top_log_odds":top["log_odds"],"top_gene_count":len(top["genes"]),"top_evidence_count":len(top["evidence_ledger"]),"top_matched_phenotype_count":len(top["matched_phenotypes"]),
    "top_contradiction_count":len(top["contradicted_phenotypes"]),"top_has_genomic_evidence":any(x["evidence"]=="genomic_variant" for x in top["evidence_ledger"]),
    "top_has_multiomic_evidence":any(x["evidence"]=="multi_omic" for x in top["evidence_ledger"]),"second_disease":c[1]["disease"],"second_posterior":c[1]["posterior"],
    "posterior_margin":top["posterior"]-c[1]["posterior"],"posterior_above_half_count":sum(x["posterior"]>.5 for x in c),"posterior_above_tenth_count":sum(x["posterior"]>.1 for x in c),
    "disease_with_any_match_count":sum(bool(x["matched_phenotypes"]) for x in c),"disease_with_contradiction_count":sum(bool(x["contradicted_phenotypes"]) for x in c),
    "variant_count":len(variants),"variant_gene_count":len(genes),"variant_missing_gene_count":sum(not v.get("gene") for v in variants),"pathogenic_variant_count":sum(x=="pathogenic" for x in classifications),
    "likely_pathogenic_variant_count":sum(x=="likely_pathogenic" for x in classifications),"vus_variant_count":sum(x in {"vus","uncertain_significance"} for x in classifications),
    "benign_variant_count":sum("benign" in x for x in classifications),"rare_variant_count":sum(x<.01 for x in af),"ultrarare_variant_count":sum(x<.0001 for x in af),
    "common_variant_count":sum(x>.01 for x in af),"variant_with_frequency_count":sum("allele_frequency" in v for v in variants),"variant_with_hgvs_count":sum(bool(v.get("hgvs")) for v in variants),
    "variant_with_id_count":sum(bool(v.get("id")) for v in variants),"candidate_gene_variant_count":sum(bool(genes&set(x["genes"])) for x in c),"omics_modality_count":len(omics),
    "disrupted_gene_count":len(omics.get("disrupted_genes",[])),"expression_outlier_count":len(omics.get("expression_outliers",[])),"metabolite_abnormality_count":len(omics.get("metabolite_abnormalities",[])),
    "protein_abnormality_count":len(omics.get("protein_abnormalities",[])),"methylation_signature_present":bool(omics.get("methylation_signature")),"top_treatment_count":len(_treatments(top["disease"])),
    "top_has_targeted_treatment":any(x["type"]=="targeted" for x in _treatments(top["disease"])),"top_has_confirmatory_gene":bool(top["genes"]),"phenotype_only_case":not variants and not omics,
    "genome_only_case":bool(variants) and not symptoms,"multiomic_case":bool(omics),"negative_evidence_used":bool(neg),"ranking_explainable":all("evidence_ledger" in x for x in c),
    "review_priority_high":bool(top["posterior"]>.5 and any(x["evidence"]=="genomic_variant" for x in top["evidence_ledger"])),"reanalysis_recommended":bool(top["posterior"]<.5),
    "data_completeness_score":sum([bool(symptoms),bool(variants),bool(omics),bool(negative_symptoms)])/4,
    }
    assert len(out)==54
    return out
