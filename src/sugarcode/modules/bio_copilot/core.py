from __future__ import annotations

# small grounded knowledge slice (the local stand-in for PubMed/UniProt grounding)
GENES = {
    "TP53": {"protein_len": 393, "domains": {"DBD": (102, 292), "TAD": (1, 61)},
             "hotspots": [175, 245, 248, 273, 282],
             "pathway": "DNA damage response / apoptosis"},
    "BRCA1": {"protein_len": 1863, "domains": {"RING": (1, 109), "BRCT": (1646, 1863)},
              "hotspots": [61, 1699, 1756], "pathway": "homologous recombination repair"},
    "KRAS": {"protein_len": 189, "domains": {"G-domain": (1, 166)},
             "hotspots": [12, 13, 61], "pathway": "MAPK signaling"},
}
CODON_TABLE = {"R": "CGN", "H": "CAY", "G": "GGN", "D": "GAY", "C": "TGY", "W": "TGG",
               "L": "CTN", "P": "CCN", "A": "GCN", "S": "TCN", "T": "ACN", "V": "GTN"}
HYDROPHOB = set("AILMFWVYV")


def mutation_to_phenotype(gene: str, ref_aa: str, pos: int, alt_aa: str) -> dict:
    """Directed computation graph: variant -> domain -> structure -> pathway -> phenotype.

    Each node is a small real computation; inconsistencies between nodes are
    flagged instead of blended.
    """
    if gene not in GENES:
        raise KeyError(f"gene {gene!r} not grounded; have {sorted(GENES)}")
    g = GENES[gene]
    if not (1 <= pos <= g["protein_len"]):
        raise ValueError(f"{gene} is {g['protein_len']} aa")
    nodes = []
    # node 1: variant consequence
    domain = next((d for d, (a, b) in g["domains"].items() if a <= pos <= b), None)
    hotspot = pos in g["hotspots"]
    nodes.append({"node": "variant_annotation",
                  "consequence": "missense", "domain": domain, "hotspot": hotspot,
                  "codon_change": f"{CODON_TABLE.get(ref_aa, '???')}->{CODON_TABLE.get(alt_aa, '???')}"})
    # node 2: structural perturbation (ddG proxy)
    d_hydro = (alt_aa in HYDROPHOB) - (ref_aa in HYDROPHOB)
    ddg = round(0.8 * abs(d_hydro) + (1.2 if hotspot else 0.3) + (0.5 if domain else 0.0), 2)
    destabilizing = ddg > 1.0
    nodes.append({"node": "structural_perturbation", "ddG_estimate_kcal": ddg,
                  "destabilizing": destabilizing,
                  "mechanism": "hydrophobic core swap" if d_hydro else "surface/charge change"})
    # node 3: pathway flux effect
    flux_impact = round(min(1.0, ddg / 3 * (1.5 if hotspot else 0.8)), 2)
    nodes.append({"node": "pathway_effect", "pathway": g["pathway"],
                  "flux_disruption": flux_impact})
    # node 4: phenotype with uncertainty
    risk = round(0.15 + 0.5 * flux_impact + (0.25 if hotspot else 0.0), 2)
    phenotype = ("likely pathogenic" if risk > 0.7 else
                 "uncertain significance" if risk > 0.4 else "likely tolerated")
    nodes.append({"node": "phenotype_inference", "phenotype": phenotype,
                  "risk_score": min(risk, 1.0)})
    # reconciliation: structurally tolerated but pathway-disruptive, or vice versa
    flags = []
    if not destabilizing and flux_impact > 0.4:
        flags.append("structure tolerated but pathway disrupted - functional assay needed")
    if destabilizing and flux_impact < 0.3:
        flags.append("destabilizing yet low predicted pathway impact - possible aggregation route")
    return {
        "variant": f"{gene} {ref_aa}{pos}{alt_aa}",
        "computation_graph": nodes,
        "phenotype": phenotype, "risk_score": min(risk, 1.0),
        "inconsistency_flags": flags,
        "suggested_experiments": ["saturation mutagenesis at the locus",
                                  "thermal shift assay for stability",
                                  f"reporter of {g['pathway']} activity"],
        "uncertainty": {"data_sparsity": "medium", "model_class": "biophysical priors, not learned weights"},
    }


def to_fasta(seq_id: str, protein: str) -> str:
    lines = [f">{seq_id}"] + [protein[i:i + 60] for i in range(0, len(protein), 60)]
    return "\n".join(lines) + "\n"


def to_pdb(protein: str, chain: str = "A") -> str:
    """Minimal valid PDB ATOM records (CA-only trace along a helix)."""
    import math
    rows = []
    for i, aa in enumerate(protein[:60], 1):
        x = 3.8 * i * math.cos(i * 1.745)
        y = 3.8 * i * math.sin(i * 1.745)
        z = 1.5 * i
        rows.append(f"ATOM  {i:5d}  CA  ALA {chain}{i:4d}    "
                    f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           C  ")
    rows.append("END")
    return "\n".join(rows) + "\n"


def answer(question: str) -> dict:
    """Route a natural-language question to the right pipeline or knowledge slice."""
    q = question.lower()
    for gene in GENES:
        if gene.lower() in q:
            info = GENES[gene]
            live = live_gene_context(gene)
            grounded = (f"Live UniProt: {live.get('protein_name', '?')}, "
                        f"{live.get('length', info['protein_len'])} aa"
                        if live.get("source") == "UniProt (live)"
                        else f"local slice ({live.get('warning', 'live unavailable')})")
            return {"route": "gene_knowledge", "gene": gene,
                    "grounding": live.get("source"),
                    "answer": (f"{gene}: {grounded}. Local: {info['protein_len']} aa, domains "
                               f"{list(info['domains'])}, hotspots {info['hotspots']}; "
                               f"pathway: {info['pathway']}"),
                    "followups": ["run mutation_to_phenotype for a specific variant",
                                  "design CRISPR guides via CRISPR Opt"]}
    if "mutation" in q or "variant" in q:
        return {"route": "variant_pipeline",
                "answer": "use mutation_to_phenotype(gene, ref, pos, alt) for the full DAG",
                "followups": ["structural node -> Protein Painter", "pathway node -> Virtual Cell"]}
    if "fasta" in q or "pdb" in q:
        return {"route": "structured_output",
                "answer": "to_fasta / to_pdb generate valid structured files"}
    return {"route": "literature_synthesis",
            "answer": ("no grounded local hit; in deployment this route queries PubMed E-utilities "
                       "and synthesizes with citations - local graph has genes: "
                       + ", ".join(sorted(GENES))),
            "followups": ["narrow the question to a gene or variant"]}


def live_gene_context(gene: str, offline: bool = False) -> dict:
    """Ground a gene query in live UniProt data; local knowledge slice is the
    fallback, never a silent substitute - the source is named either way."""
    from ...bio import uniprot
    try:
        rec = uniprot.search(gene, offline=offline)
        if rec:
            domains = [f for f in rec["features"] if f["type"] in ("Domain", "Region")]
            return {"gene": gene, "source": "UniProt (live)",
                    "protein_name": rec["protein_name"], "length": rec["length"],
                    "mass_Da": rec["mass"], "n_features": len(rec["features"]),
                    "domains": domains[:10], "go_terms": rec["go_terms"][:10]}
    except Exception as e:
        return {"gene": gene, "source": "local knowledge slice",
                "warning": f"live lookup failed: {type(e).__name__}: {e}",
                "local": GENES.get(gene)}
    return {"gene": gene, "source": "local knowledge slice",
            "warning": "no reviewed UniProt entry", "local": GENES.get(gene)}
