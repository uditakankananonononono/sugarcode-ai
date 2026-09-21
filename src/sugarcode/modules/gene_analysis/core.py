from __future__ import annotations
from ...bio.sequence import clean_dna, gc_content, translate, molecular_weight, orfs
from ..crispr_opt.core import design_guides
from ..openclinvar.core import interpret_variant
from ..dark_genome.core import decode


def gene_profile(symbol: str, genomic_seq: str, promoter_span: tuple[int, int] | None = None,
                 variants: list[dict] | None = None, publications: list[int] | None = None) -> dict:
    """High-fidelity biological profile of a gene locus.

    Integrates: sequence composition, ORF/protein stats, regulatory landscape,
    variant interpretations, CRISPR target designs and publication trend bins.
    External NCBI/UniProt/ClinVar connectors are a later drop; this computes
    everything derivable from the sequence itself.
    """
    s = clean_dna(genomic_seq)
    found_orfs = orfs(s, min_aa=30)
    longest = max(found_orfs, key=lambda o: o["aa_length"], default=None)
    protein = longest["protein"] if longest else ""
    regulatory = decode(s, coding_spans=[(o["start"], o["end"]) for o in found_orfs])
    crispr = design_guides(s, background=s, top_n=5)
    var_results = []
    for v in (variants or []):
        var_results.append(interpret_variant(symbol, v["variant"],
                                             consequence=v.get("consequence"),
                                             allele_frequency=v.get("allele_frequency"),
                                             functional_score=v.get("functional_score")))
    return {
        "symbol": symbol,
        "locus": {"length": len(s), "gc_content": round(gc_content(s), 4)},
        "protein": ({"aa_length": longest["aa_length"],
                     "molecular_weight_da": round(molecular_weight(protein), 1),
                     "strand": longest["strand"], "span": [longest["start"], longest["end"]]}
                    if longest else None),
        "regulatory_landscape": {
            "enhancer_clusters": regulatory["enhancer_clusters"],
            "cpg_islands": regulatory["cpg_islands"],
            "tf_motif_count": len(regulatory["tf_motif_hits"]),
        },
        "variants": var_results,
        "crispr_targets": crispr["guides"],
        "publication_trend": _pub_trend(publications or []),
        "pathway_links": _pathway_links(symbol),
    }


def _pub_trend(years: list[int]) -> dict:
    if not years:
        return {"note": "no publication data supplied"}
    bins: dict[int, int] = {}
    for y in years:
        bins[y // 5 * 5] = bins.get(y // 5 * 5, 0) + 1
    return {"by_half_decade": dict(sorted(bins.items())), "total": len(years)}


def _pathway_links(symbol: str) -> list[dict]:
    known = {
        "TP53": ["DNA damage response", "apoptosis", "cell-cycle checkpoint"],
        "BRCA1": ["homologous recombination repair", "G2/M checkpoint"],
        "CFTR": ["chloride transport", "epithelial fluid secretion"],
        "HBB": ["oxygen transport", "erythrocyte physiology"],
        "EGFR": ["RTK signaling", "MAPK cascade", "cell proliferation"],
    }
    return [{"pathway": p, "source": "built-in reference"} for p in known.get(symbol.upper(), [])]


def live_gene_profile(symbol: str, organism: str = "human", offline: bool = False) -> dict:
    """Live multi-source gene profile: NCBI Gene + UniProt, merged.

    Falls back per-source: a source that fails is reported as unavailable,
    never silently dropped or invented.
    """
    from ...bio import entrez, uniprot
    out = {"symbol": symbol, "organism": organism, "sources": {}}
    try:
        uid = entrez.gene_id(symbol, organism, offline=offline)
        if uid:
            summ = entrez.esummary("gene", [uid], offline=offline)[uid]
            out["sources"]["ncbi_gene"] = {
                "uid": uid, "name": summ.get("name"),
                "description": summ.get("description"),
                "chromosome": summ.get("chromosome"),
                "map_location": summ.get("maplocation"),
                "aliases": summ.get("otheraliases", ""),
            }
        else:
            out["sources"]["ncbi_gene"] = {"error": "symbol not found"}
    except Exception as e:  # connector failure is reported, not hidden
        out["sources"]["ncbi_gene"] = {"error": f"{type(e).__name__}: {e}"}
    try:
        org_id = 9606 if organism == "human" else 10090
        rec = uniprot.search(symbol, organism_id=org_id, offline=offline)
        out["sources"]["uniprot"] = rec or {"error": "no reviewed entry"}
    except Exception as e:
        out["sources"]["uniprot"] = {"error": f"{type(e).__name__}: {e}"}
    # local analysis still runs on the fetched sequence when available
    seq = (out["sources"].get("uniprot") or {}).get("sequence", "")
    if seq:
        out["protein_stats"] = {
            "length": len(seq),
            "hydrophobic_fraction": round(sum(1 for a in seq if a in "AILMFWVY") / len(seq), 3),
            "charged_fraction": round(sum(1 for a in seq if a in "DEKRH") / len(seq), 3),
        }
    return out
