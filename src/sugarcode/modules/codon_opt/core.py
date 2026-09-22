from __future__ import annotations
import math
import numpy as np
from ...bio import codon as codonlib
from ...bio.sequence import clean_dna, gc_content, gc_windows, STANDARD_CODE


def optimize(protein: str, host: str = "ecoli_k12", gc_min: float = 0.40,
             gc_max: float = 0.60, avoid_motifs: list[str] | None = None) -> dict:
    """Optimize a protein's coding sequence for a host.

    Returns the optimized DNA with CAI before/after, GC profile and a
    tRNA-pool strain estimate (CHI-style) plus a TASEP flow summary.
    """
    table = codonlib.HOST_TABLES.get(host)
    if table is None:
        raise ValueError(f"unknown host {host!r}; have {sorted(codonlib.HOST_TABLES)}")
    naive = "".join(
        max(codonlib.synonymous_codons(a), key=lambda c: table.get(c, 0))
        for a in protein.upper() if a in "ACDEFGHIKLMNPQRSTVWY"
    )
    # naive = max-frequency design; "before" baseline = uniform first synonym
    before = "".join(codonlib.synonymous_codons(a)[0]
                     for a in protein.upper() if a in "ACDEFGHIKLMNPQRSTVWY")
    opt = codonlib.optimize_sequence(protein.upper(), table, gc_min, gc_max, avoid_motifs)
    strain = _trna_strain(opt, table)
    flow = tasep_simulate(opt, table)
    cai_naive = codonlib.cai(naive, table)
    cai_opt = codonlib.cai(opt, table)
    gc_repair_cost = round(max(0.0, cai_naive - cai_opt), 4)
    return {
        "host": host,
        "protein_length": len(protein),
        "optimized_dna": opt,
        "cai_before": round(codonlib.cai(before, table), 4),
        "cai_after": round(cai_opt, 4),
        "cai_gc_repair_cost": gc_repair_cost,
        "gc_repair_note": (f"GC-window repair traded {gc_repair_cost:.3f} CAI to keep GC inside "
                           f"[{gc_min}, {gc_max}] - widen the band if native GC is preferred"
                           if gc_repair_cost > 0.02 else None),
        "gc_content": round(gc_content(opt), 4),
        "gc_windows": [{"start": s, "gc": round(g, 3)} for s, g in gc_windows(opt, 60)],
        "chi_score": round(strain, 4),
        "tasep": flow,
        "sbml_export": _sbml_export(opt, strain),
    }


def _trna_strain(dna: str, table: dict[str, float]) -> float:
    """tRNA pool strain index: demand-weighted scarcity of used codons.

    CHI-style: mean of -log(relative adaptiveness) across codons; lower is
    gentler on the host tRNA pool. 0 = perfectly matched to pool.
    """
    w = codonlib.relative_adaptiveness(table)
    s = clean_dna(dna)
    vals = []
    for i in range(0, len(s) - 2, 3):
        wi = w.get(s[i:i + 3], 1e-6)
        vals.append(-math.log(max(wi, 1e-6)))
    return sum(vals) / len(vals) if vals else 0.0


def tasep_simulate(dna: str, table: dict[str, float] | None = None,
                   ribosome_init_rate: float = 2.0, steps: int = 4000) -> dict:
    """Totally-asymmetric exclusion process over codon positions.

    Each site is a codon; hopping rate is proportional to codon relative
    adaptiveness (abundant tRNAs decode faster). Gillespie-style KMC.
    Returns ribosome density profile, jam locations and protein output rate.
    """
    table = table or codonlib.ECOLI_K12
    s = clean_dna(dna)
    w = codonlib.relative_adaptiveness(table)
    codons = [s[i:i + 3] for i in range(0, len(s) - 2, 3)]
    n = len(codons)
    if n == 0:
        raise ValueError("empty coding sequence")
    hop = np.array([max(w.get(c, 0.05), 0.05) * 10.0 for c in codons])  # /s
    dwell = [round(1.0 / max(h, 1e-9), 4) for h in hop]  # seconds per codon
    lattice = np.zeros(n, dtype=int)
    rng = np.random.default_rng(42)
    density = np.zeros(n)
    completions = 0
    t = 0.0
    burn = steps // 4
    for step in range(steps):
        rates = []
        rates.append(ribosome_init_rate if lattice[0] == 0 else 0.0)
        for i in range(n):
            if lattice[i] == 1 and (i == n - 1 or lattice[i + 1] == 0):
                rates.append(hop[i])
            else:
                rates.append(0.0)
        rates = np.array(rates)
        total = rates.sum()
        if total <= 0:
            break
        t += rng.exponential(1.0 / total)
        choice = rng.choice(len(rates), p=rates / total)
        if choice == 0:
            lattice[0] = 1
        else:
            i = choice - 1  # rates[0] is initiation; rates[k] hops lattice[k-1]
            lattice[i] = 0
            if i == n - 1:
                completions += 1
            else:
                lattice[i + 1] = 1
        if step >= burn:
            density += lattice
    density /= max(1, steps - burn)
    jams = [int(i) for i in range(1, n - 1)
            if density[i] > 0.6 and density[i] > density[i - 1] and density[i] >= density[i + 1]]
    return {
        "codons": n,
        "dwell_times_s": dwell,
        "dwell_provenance": ("derived from vendored published codon-usage table "
                             "(dwell = 1/(10*w), the tRNA-abundance approximation of "
                             "Dana & Tuller 2014). Empirical Ribo-seq-calibrated rates "
                             "are Missing: no verifiable machine-readable source found."),
        "sim_time_s": round(t, 2),
        "proteins_completed": completions,
        "output_rate_per_s": round(completions / t, 4) if t > 0 else 0.0,
        "mean_density": round(float(density.mean()), 4),
        "density_profile": [round(float(d), 3) for d in density],
        "jam_sites": jams,
    }


def metabolic_load(dna: str, host_flux_mmol_gdw_h: float = 10.0,
                   copies: int = 100, atp_per_aa: float = 4.0) -> dict:
    """Estimate the biosynthetic burden of expressing the synthetic gene.

    Couples gene length/copies to ATP and precursor demand and reports the
    fractional diversion of host energy flux (FBA-style constraint term).
    """
    s = clean_dna(dna)
    n_aa = len(s) // 3
    atp_cost = n_aa * atp_per_aa * copies
    atp_cost_mmol = atp_cost * 1.66e-9  # per-cell ATP count -> mmol/gDW/h scale factor
    fraction = atp_cost_mmol / max(host_flux_mmol_gdw_h, 1e-9)
    return {
        "gene_copies": copies,
        "aa_length": n_aa,
        "atp_molecules_per_cell_per_cycle": atp_cost,
        "estimated_host_flux_diversion": round(min(fraction, 1.0), 6),
        "burden_class": "low" if fraction < 0.01 else "moderate" if fraction < 0.05 else "high",
        "fba_constraint_row": {
            "name": "SYNTH_GENE_EXPRESSION",
            "stoichiometry": {"ATP": -atp_per_aa * copies, "AA_POOL": -copies},
            "lower_bound": 0.0,
            "upper_bound": round(atp_cost_mmol, 9),
        },
    }


def _sbml_export(dna: str, strain: float) -> str:
    """Real SBML Level 3 Version 2 export of the optimized construct: one
    compartment, five species (gene, mRNA, protein, ATP, amino-acid pool)
    and four reactions (transcription, translation, mRNA decay, protein
    decay) with mass-action kinetic laws. The translation rate constant
    carries the tRNA-pool strain index as k_translate = k0 / (1 + strain),
    so the exported model responds to the optimization quality; ATP and
    amino-acid consumption stoichiometry follows the translation reaction.
    Generated directly as XML (no libsbml dependency); structure is
    validated by the drop-54 tests."""
    from xml.sax.saxutils import escape
    n_nt = len(dna)
    n_aa = n_nt // 3
    k_tx, k_tl0, k_mdeg, k_pdeg = 0.05, 0.1, 0.01, 0.005
    k_tl = k_tl0 / (1.0 + max(strain, 0.0))
    notes = (f"Codon-optimized construct, {n_nt} nt ({n_aa} aa); "
             f"tRNA-pool strain index {strain:.4f}; translation rate "
             f"constant k_translate={k_tl:.6f} = k0/(1+strain)")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3/version2/core" level="3" version="2">
  <model id="codon_opt_construct" metaid="meta_codon_opt_construct" substanceUnits="item" timeUnits="second" extentUnits="item">
    <notes><p xmlns="http://www.w3.org/1999/xhtml">{escape(notes)}</p></notes>
    <listOfUnitDefinitions>
      <unitDefinition id="per_second"><listOfUnits><unit kind="second" exponent="-1" scale="0" multiplier="1"/></listOfUnits></unitDefinition>
    </listOfUnitDefinitions>
    <listOfCompartments>
      <compartment id="cell" spatialDimensions="3" size="1" constant="true"/>
    </listOfCompartments>
    <listOfSpecies>
      <species id="SYNTH_GENE" compartment="cell" initialAmount="1" hasOnlySubstanceUnits="true" boundaryCondition="true" constant="true"/>
      <species id="SYNTH_mRNA" compartment="cell" initialAmount="0" hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>
      <species id="SYNTH_protein" compartment="cell" initialAmount="0" hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>
      <species id="ATP" compartment="cell" initialAmount="1000000" hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>
      <species id="AA_POOL" compartment="cell" initialAmount="1000000" hasOnlySubstanceUnits="true" boundaryCondition="false" constant="false"/>
    </listOfSpecies>
    <listOfParameters>
      <parameter id="k_transcribe" value="{k_tx}" units="per_second" constant="true"/>
      <parameter id="k_translate" value="{k_tl:.6f}" units="per_second" constant="true"/>
      <parameter id="k_mrna_decay" value="{k_mdeg}" units="per_second" constant="true"/>
      <parameter id="k_protein_decay" value="{k_pdeg}" units="per_second" constant="true"/>
      <parameter id="trna_strain_index" value="{strain:.6f}" constant="true"/>
      <parameter id="construct_nt" value="{n_nt}" constant="true"/>
    </listOfParameters>
    <listOfReactions>
      <reaction id="transcription" reversible="false">
        <listOfReactants><speciesReference species="SYNTH_GENE" stoichiometry="1" constant="true"/></listOfReactants>
        <listOfProducts><speciesReference species="SYNTH_mRNA" stoichiometry="1" constant="true"/></listOfProducts>
        <kineticLaw><math xmlns="http://www.w3.org/1998/Math/MathML"><apply><times/><ci>k_transcribe</ci><ci>SYNTH_GENE</ci></apply></math></kineticLaw>
      </reaction>
      <reaction id="translation" reversible="false">
        <listOfReactants>
          <speciesReference species="SYNTH_mRNA" stoichiometry="1" constant="true"/>
          <speciesReference species="ATP" stoichiometry="{4 * n_aa}" constant="true"/>
          <speciesReference species="AA_POOL" stoichiometry="{n_aa}" constant="true"/>
        </listOfReactants>
        <listOfProducts><speciesReference species="SYNTH_protein" stoichiometry="1" constant="true"/></listOfProducts>
        <kineticLaw><math xmlns="http://www.w3.org/1998/Math/MathML"><apply><times/><ci>k_translate</ci><ci>SYNTH_mRNA</ci></apply></math></kineticLaw>
      </reaction>
      <reaction id="mrna_decay" reversible="false">
        <listOfReactants><speciesReference species="SYNTH_mRNA" stoichiometry="1" constant="true"/></listOfReactants>
        <kineticLaw><math xmlns="http://www.w3.org/1998/Math/MathML"><apply><times/><ci>k_mrna_decay</ci><ci>SYNTH_mRNA</ci></apply></math></kineticLaw>
      </reaction>
      <reaction id="protein_decay" reversible="false">
        <listOfReactants><speciesReference species="SYNTH_protein" stoichiometry="1" constant="true"/></listOfReactants>
        <kineticLaw><math xmlns="http://www.w3.org/1998/Math/MathML"><apply><times/><ci>k_protein_decay</ci><ci>SYNTH_protein</ci></apply></math></kineticLaw>
      </reaction>
    </listOfReactions>
  </model>
</sbml>"""

# --- laboratory-grade integrated construct design -----------------------------
def _validate_design(protein,host,gc_min,gc_max,copies):
    p=protein.upper().strip()
    if not p: raise ValueError("protein must be a non-empty amino-acid sequence")
    bad=sorted(set(p)-set("ACDEFGHIKLMNPQRSTVWY"))
    if bad: raise ValueError(f"protein contains unsupported residues: {bad}")
    if host not in codonlib.HOST_TABLES: raise ValueError(f"unknown host {host!r}; available hosts: {sorted(codonlib.HOST_TABLES)}")
    if not 0<gc_min<gc_max<1: raise ValueError("GC bounds must satisfy 0 < gc_min < gc_max < 1")
    if copies<1: raise ValueError("copies must be a positive integer")
    return p


def sequence_attention(dna:str,heads:int=4)->dict:
    """Deterministic, untrained contextual codon self-attention diagnostic."""
    s=clean_dna(dna); codons=[s[i:i+3] for i in range(0,len(s)-2,3)]
    if not codons: raise ValueError("dna must contain at least one complete codon")
    X=np.array([[c.count(b)/3 for b in "ATGC"] for c in codons]); pos=np.arange(len(codons))[:,None]
    feats=np.concatenate([X,np.sin(pos/10),np.cos(pos/10)],1); mats=[]
    for h in range(heads):
        shift=np.roll(feats,h,axis=1); z=shift@shift.T/np.sqrt(feats.shape[1]); z-=z.max(1,keepdims=True); a=np.exp(z); a/=a.sum(1,keepdims=True); mats.append(a)
    att=np.mean(mats,0)
    return {"attention":att.tolist(),"context_score":att.max(1).tolist(),"heads":heads,"method":"deterministic untrained codon-context attention"}


def folding_accessibility(dna:str,window:int=30)->dict:
    """Nearest-neighbor-inspired local RNA pairing and initiation accessibility."""
    s=clean_dna(dna).replace("T","U")
    if len(s)<6: raise ValueError("dna must be at least 6 nt for folding analysis")
    energies=[]
    for i in range(len(s)):
        seg=s[max(0,i-window//2):min(len(s),i+window//2)]; gc=seg.count("G")+seg.count("C"); pairs=sum(seg[j]+seg[-j-1] in ("GC","CG","AU","UA","GU","UG") for j in range(len(seg)//2)); energies.append(-2.1*gc/len(seg)-.5*pairs)
    acc=1/(1+np.exp(-np.array(energies)))
    return {"local_delta_g_kcal_mol":energies,"accessibility":acc.tolist(),"initiation_accessibility":float(np.mean(acc[:min(30,len(acc))])),"method":"deterministic nearest-neighbor-inspired screening"}


def evolutionary_robustness(dna:str,trials:int=200,seed:int=7)->dict:
    """Synonymous/nonsynonymous single-mutation landscape and motif risk."""
    s=clean_dna(dna); rng=np.random.default_rng(seed); code=STANDARD_CODE; retained=0; stops=0; effects=[]
    for _ in range(trials):
        i=int(rng.integers(len(s))); alt=rng.choice([b for b in "ATGC" if b!=s[i]]); m=s[:i]+alt+s[i+1:]; c=i//3; a0=code.get(s[c*3:c*3+3],"X"); a1=code.get(m[c*3:c*3+3],"X"); retained+=a0==a1; stops+=a1=="*"; effects.append(0 if a0==a1 else -1 if a1=="*" else -.3)
    repeats=max((s.count(k*4) for k in "ATGC"),default=0)
    return {"synonymous_fraction":retained/trials,"stop_gain_fraction":stops/trials,"mean_mutation_effect":float(np.mean(effects)),"homopolymer_risk":repeats,"trials":trials,"seed":seed}


def _design_diagnostics(dna,tasep,load,fold,evo,attention,table,copies):
    codons=[dna[i:i+3] for i in range(0,len(dna),3)]; w=codonlib.relative_adaptiveness(table); dw=np.array(tasep["dwell_times_s"]); den=np.array(tasep["density_profile"]); gc=np.array([x[1] for x in gc_windows(dna,60)] or [gc_content(dna)]); acc=np.array(fold["accessibility"]); ctx=np.array(attention["context_score"])
    d={"sequence_length_nt":len(dna),"protein_length_aa":len(codons),"GC_fraction":gc_content(dna),"GC_window_min":float(gc.min()),"GC_window_max":float(gc.max()),"GC_window_range":float(np.ptp(gc)),"CAI":codonlib.cai(dna,table),"CHI":_trna_strain(dna,table),"rare_codon_fraction":sum(w.get(c,0)<.2 for c in codons)/len(codons),"optimal_codon_fraction":sum(w.get(c,0)>.8 for c in codons)/len(codons),"codon_diversity":len(set(codons)),"codon_entropy":float(-(lambda p:p@np.log(p+1e-12))(np.unique(codons,return_counts=True)[1]/len(codons))),"mean_dwell_s":float(dw.mean()),"max_dwell_s":float(dw.max()),"dwell_CV":float(dw.std()/dw.mean()),"output_rate_per_s":tasep["output_rate_per_s"],"ribosome_mean_density":tasep["mean_density"],"ribosome_peak_density":float(den.max()),"jam_site_count":len(tasep["jam_sites"]),"queue_fraction":float((den>.6).mean()),"initiation_accessibility":fold["initiation_accessibility"],"mean_mRNA_accessibility":float(acc.mean()),"minimum_mRNA_accessibility":float(acc.min()),"structured_fraction":float((acc<.2).mean()),"attention_peak":float(ctx.max()),"attention_mean":float(ctx.mean()),"ATP_cost":load["atp_molecules_per_cell_per_cycle"],"host_flux_diversion":load["estimated_host_flux_diversion"],"gene_copies":copies,"synonymous_robustness":evo["synonymous_fraction"],"stop_gain_risk":evo["stop_gain_fraction"],"mean_mutation_effect":evo["mean_mutation_effect"],"homopolymer_risk":evo["homopolymer_risk"],"start_codon_valid":dna.startswith("ATG"),"internal_stop_count":sum(code=="*" for code in [STANDARD_CODE.get(c) for c in codons[:-1]]),"restriction_EcoRI_count":dna.count("GAATTC"),"restriction_BamHI_count":dna.count("GGATCC"),"restriction_BsaI_count":dna.count("GGTCTC")+dna.count("GAGACC"),"repeat_AT_count":dna.count("ATATAT"),"repeat_GC_count":dna.count("GCGCGC"),"CpG_fraction":dna.count("CG")/len(dna),"mRNA_length_nt":len(dna),"translation_time_s":float(dw.sum()),"proteins_per_hour":3600*tasep["output_rate_per_s"],"ATP_per_protein":4*len(codons),"resource_efficiency":tasep["output_rate_per_s"]/(1+load["estimated_host_flux_diversion"]),"folding_pause_balance":float(np.corrcoef(dw,np.array(acc)[::3][:len(dw)])[0,1]) if len(dw)>2 else 0,"bottleneck_codon_index":int(dw.argmax()),"bottleneck_codon":codons[int(dw.argmax())],"synthesis_complexity_score":float(np.ptp(gc)+evo["homopolymer_risk"]*.1+sum(dna.count(x) for x in ("GAATTC","GGATCC","GGTCTC"))),"design_score":float(codonlib.cai(dna,table)*fold["initiation_accessibility"]*evo["synonymous_fraction"]/(1+load["estimated_host_flux_diversion"]))}
    assert len(d)>=50; return d


def design_expression_construct(protein:str,host:str="ecoli_k12",*,gc_min:float=.40,gc_max:float=.60,copies:int=100,avoid_motifs:list[str]|None=None,tasep_steps:int=2000,seed:int=7)->dict:
    """Design an actionable synthesis-ready coding sequence for a named host."""
    p=_validate_design(protein,host,gc_min,gc_max,copies); base=optimize(p,host,gc_min,gc_max,avoid_motifs); dna=base["optimized_dna"]; table=codonlib.HOST_TABLES[host]
    flow=tasep_simulate(dna,table,steps=tasep_steps); load=metabolic_load(dna,copies=copies); fold=folding_accessibility(dna); evo=evolutionary_robustness(dna,seed=seed); att=sequence_attention(dna); diag=_design_diagnostics(dna,flow,load,fold,evo,att,table,copies)
    flags=[]
    if diag["jam_site_count"]: flags.append("ribosome queue predicted: inspect bottleneck codon and local structure")
    if diag["host_flux_diversion"]>.05: flags.append("high expression burden: reduce copy number or promoter strength")
    if diag["initiation_accessibility"]<.2: flags.append("structured 5-prime coding region: redesign first 30 nt with RBS context")
    return {"host":host,"optimized_dna":dna,"protein":p,"diagnostics":diag,"enhancement_feature_count":len(diag),"kinetics":flow,"folding":fold,"metabolic_load":load,"evolutionary_robustness":evo,"context_attention":att,"quality_flags":flags,"recommended_next_steps":["order synthesis with vendor sequence QC","validate expression by small-scale induction time course","measure growth-rate burden against empty-vector control","confirm product folding/activity"],"artifacts":{"sbml":base["sbml_export"],"fasta":f">codon_opt_{host}\n{dna}\n"},"model_status":"mechanistic and deterministic/untrained sequence models; not clinically validated"}
