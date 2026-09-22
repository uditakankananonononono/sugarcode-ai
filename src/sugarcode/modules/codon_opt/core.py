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
