from __future__ import annotations
from ...bio.sequence import clean_dna, gc_content
from ..crispr_opt.core import design_guides

PHAGE_BACKBONES = {
    "M13": {"type": "filamentous", "capacity_kb": 6.4, "lytic": False, "host_range": "narrow (F+ E. coli)"},
    "T4": {"type": "myovirus", "capacity_kb": 10.0, "lytic": True, "host_range": "E. coli broad"},
    "T7": {"type": "podovirus", "capacity_kb": 4.0, "lytic": True, "host_range": "E. coli (fast lysis)"},
    "lambda": {"type": "siphovirus", "capacity_kb": 8.0, "lytic": False, "host_range": "E. coli K12"},
    "P1": {"type": "myovirus", "capacity_kb": 15.0, "lytic": True, "host_range": "enteric broad"},
}
RESISTANCE_TARGETS = {
    "NDM-1": {"gene_class": "carbapenemase", "essentiality": 0.7},
    "mcr-1": {"gene_class": "colistin resistance", "essentiality": 0.6},
    "vanA": {"gene_class": "vancomycin resistance", "essentiality": 0.65},
    "gyrA": {"gene_class": "essential - fluoroquinolone target", "essentiality": 0.95},
    "rpoB": {"gene_class": "essential - rifampin target", "essentiality": 0.95},
}


def design_phage(target_gene_seq: str, resistance_marker: str = "NDM-1",
                 backbone: str | None = None,
                 background_genome: str | None = None) -> dict:
    """Engineer a phage carrying CRISPR payload against a resistance gene.

    Selects backbone by payload size + host range, designs guides against the
    target gene, modifies tail-fiber host targeting, assesses community safety.

    background_genome: optional sequence the guides are screened against with
    the published CFD off-target model (e.g. the bacterial host chromosome).
    When omitted, guides are screened against the target gene itself, which
    only finds in-gene collateral sites; pass a real background for a true
    off-target screen.
    """
    s = clean_dna(target_gene_seq)
    payload_kb = 4.5  # Cas9 + guide array + selection
    if backbone is None:
        cands = [(k, v) for k, v in PHAGE_BACKBONES.items() if v["capacity_kb"] >= payload_kb and v["lytic"]]
        backbone = max(cands, key=lambda kv: kv[1]["capacity_kb"])[0] if cands else "P1"
    bb = PHAGE_BACKBONES[backbone]
    if background_genome is not None:
        screen_bg = clean_dna(background_genome)
        screen_desc = ("guides screened with the published CFD model (Doench 2016) "
                       "against the supplied background genome, perfect-match sites "
                       "included; extend to a full microbiome DB for community-scale screening")
        screened = "supplied background genome"
    else:
        screen_bg = s
        screen_desc = ("guides screened with the published CFD model (Doench 2016) against "
                       "the target gene itself (in-gene collateral sites only, each guide's "
                       "own locus excluded); no background genome supplied - pass "
                       "background_genome (e.g. the host chromosome) for a true off-target screen")
        screened = "target gene only"
    guides = design_guides(s, background=screen_bg, top_n=3)
    marker = RESISTANCE_TARGETS.get(resistance_marker, {"gene_class": "unknown", "essentiality": 0.5})
    return {
        "backbone": backbone, "backbone_properties": bb,
        "resistance_marker": resistance_marker, "marker_info": marker,
        "payload": {"cas": "SpCas9", "guides": guides["guides"],
                    "payload_kb": payload_kb, "fits": payload_kb <= bb["capacity_kb"]},
        "host_targeting": _tail_fiber(backbone),
        "specificity": {
            "kill_mechanism": "CRISPR cuts resistance gene; lytic cycle destroys host",
            "microbiome_sparing": round(0.6 + 0.3 * (1 - 0.5 * marker["essentiality"]), 2),
            "off_target_assessment": screen_desc,
            "background_screened": screened,
        },
        "engineering_steps": [
            f"clone CRISPR array into {backbone} genome via homologous recombination",
            "swap tail fiber for target serotype tropism",
            "propagate on permissive host, titer by plaque assay",
            "validate kill curve on resistant isolate (MOI 0.1-10)",
        ],
    }


def _tail_fiber(backbone: str) -> dict:
    return {"strategy": "tail-fiber swap / point mutagenesis for serotype tropism",
            "backbone_native_range": PHAGE_BACKBONES[backbone]["host_range"],
            "note": "adsorption is the host-range gate; CRISPR only acts after DNA entry"}

import math

def payload_budget(backbone, components_kb):
    if backbone not in PHAGE_BACKBONES: raise ValueError(f"unknown backbone: {backbone}")
    total=sum(float(x) for x in components_kb.values()); cap=PHAGE_BACKBONES[backbone]['capacity_kb']
    return {'total_kb':total,'capacity_kb':cap,'headroom_kb':cap-total,'fits':total<=cap,'components_kb':dict(components_kb)}

def kill_curve(moi, adsorption_rate=0.8, burst_size=50, resistant_fraction=0.0):
    if moi < 0 or not 0 <= resistant_fraction <= 1: raise ValueError('MOI must be nonnegative and resistant_fraction in [0,1]')
    infected=1-math.exp(-adsorption_rate*moi); surviving=(1-infected)*(1-resistant_fraction)+resistant_fraction
    return {'moi':moi,'infected_fraction':infected,'surviving_fraction':surviving,'effective_burst':infected*burst_size}

def escape_risk(target_count, mutation_rate=1e-7, population_size=1e9):
    if target_count < 1: raise ValueError('target_count must be >= 1')
    expected=population_size*(mutation_rate**target_count)
    return {'expected_escapees':expected,'escape_probability':1-math.exp(-expected),'assumptions':{'independent_targets':True,'mutation_rate':mutation_rate,'population_size':population_size}}

def cocktail_coverage(host_susceptibility, target_hosts=None):
    hosts=sorted({h for covered in host_susceptibility.values() for h in covered}); per={h:[p for p,c in host_susceptibility.items() if h in c] for h in hosts}
    out={'hosts':hosts,'coverage_by_host':per,'redundant_hosts':[h for h,p in per.items() if len(p)>1]}
    if target_hosts is not None:
        tset=set(target_hosts)
        out['target_hosts']=sorted(tset); out['uncovered_targets']=sorted(tset-set(hosts))
        out['coverage_fraction']=len(tset&set(hosts))/len(tset) if tset else 0.0
    else:
        # legacy denominator: the union of covered hosts, so the fraction is
        # always 1.0 when any host is covered; pass target_hosts for a
        # meaningful coverage fraction (BUG 52)
        out['coverage_fraction']=1.0 if hosts else 0.0
    return out

def forge_report(target_gene_seq, resistance_marker='NDM-1', backbone=None, background_genome=None):
    out=design_phage(target_gene_seq,resistance_marker,backbone,background_genome=background_genome)
    out['validation_scope']='Transparent sequence and capacity heuristics; no trained efficacy model and not validated for clinical use.'
    return out
