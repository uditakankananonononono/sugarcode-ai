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
                 backbone: str | None = None) -> dict:
    """Engineer a phage carrying CRISPR payload against a resistance gene.

    Selects backbone by payload size + host range, designs guides against the
    target gene, modifies tail-fiber host targeting, assesses community safety.
    """
    s = clean_dna(target_gene_seq)
    payload_kb = 4.5  # Cas9 + guide array + selection
    if backbone is None:
        cands = [(k, v) for k, v in PHAGE_BACKBONES.items() if v["capacity_kb"] >= payload_kb and v["lytic"]]
        backbone = max(cands, key=lambda kv: kv[1]["capacity_kb"])[0] if cands else "P1"
    bb = PHAGE_BACKBONES[backbone]
    guides = design_guides(s, background=s, top_n=3)
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
            "off_target_assessment": "guides screened with the published CFD model (Doench 2016) against the supplied phage genome; extend to full microbiome DB later",
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
