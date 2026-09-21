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
    return {
        "host": host,
        "protein_length": len(protein),
        "optimized_dna": opt,
        "cai_before": round(codonlib.cai(before, table), 4),
        "cai_after": round(codonlib.cai(opt, table), 4),
        "gc_content": round(gc_content(opt), 4),
        "gc_windows": [{"start": s, "gc": round(g, 3)} for s, g in gc_windows(opt, 60)],
        "chi_score": round(strain, 4),
        "tasep": flow,
        "sbml_export": _sbml_stub(opt, strain),
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
            i = choice
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


def _sbml_stub(dna: str, strain: float) -> str:
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<sbml level="3" version="2"><model id="codon_opt_construct" '
            f'metaid="cai_strain_{strain:.3f}" notes="construct length {len(dna)} bp"/></sbml>')
