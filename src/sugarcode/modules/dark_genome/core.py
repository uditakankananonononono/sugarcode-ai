from __future__ import annotations
from ...bio.sequence import clean_dna, find_motif, gc_content, orfs
from ...bio import pwm

TF_MOTIFS = {
    "AP-1": "TGACTCA", "NF-kB": "GGGRNTTTCC", "p53": "RRRCWWGYYY",
    "TATA-box": "TATAWAW", "E-box": "CANNTG", "GC-box": "GGGCGG",
    "CCAAT": "CCAAT", "HNF4": "RGGTCAAAGGTCA",
}


def _cpg_islands(s: str, window: int = 200) -> list[dict]:
    islands = []
    for i in range(0, len(s) - window + 1, window // 2):
        w = s[i:i + window]
        gc = gc_content(w)
        cpg = w.count("CG")
        g = w.count("G")
        oe = (cpg * len(w)) / max(1, (w.count("C") * g)) if g else 0
        if gc > 0.5 and oe > 0.6:
            islands.append({"start": i, "end": i + window,
                            "gc": round(gc, 3), "cpg_obs_exp": round(oe, 3)})
    # merge overlapping
    merged = []
    for isl in islands:
        if merged and isl["start"] <= merged[-1]["end"]:
            merged[-1]["end"] = isl["end"]
        else:
            merged.append(dict(isl))
    return merged


def decode(seq: str, coding_spans: list[tuple[int, int]] | None = None) -> dict:
    """Decode the regulatory landscape of a (mostly non-coding) locus."""
    s = clean_dna(seq)
    coding_spans = coding_spans or []

    def noncoding(pos: int) -> bool:
        return not any(a <= pos < b for a, b in coding_spans)

    enhancers = []
    for name, motif in TF_MOTIFS.items():
        for pos in find_motif(s, motif):
            if noncoding(pos):
                enhancers.append({"tf": name, "position": pos,
                                  "motif": s[pos:pos + len(motif)]})
    # enhancer clusters: >=3 TF hits within 500 bp
    enhancers.sort(key=lambda e: e["position"])
    clusters = []
    for e in enhancers:
        if clusters and e["position"] - clusters[-1]["end"] < 500:
            clusters[-1]["hits"].append(e)
            clusters[-1]["end"] = e["position"]
        else:
            clusters.append({"start": e["position"], "end": e["position"], "hits": [e]})
    enh_clusters = [c for c in clusters if len(c["hits"]) >= 3]

    nc_orfs = [o for o in orfs(s, min_aa=20) if noncoding(o["start"])]
    lnc_candidates = [{"start": o["start"], "end": o["end"], "strand": o["strand"]}
                      for o in nc_orfs if o["aa_length"] < 100]

    formatted_clusters = [
        {"start": c["start"], "end": c["end"], "n_motifs": len(c["hits"]),
         "tfs": sorted({h["tf"] for h in c["hits"]})} for c in enh_clusters
    ]
    return {
        "length": len(s),
        "gc_content": round(gc_content(s), 4),
        "tf_motif_hits": enhancers,
        "enhancer_clusters": formatted_clusters,
        "cpg_islands": _cpg_islands(s),
        "lncrna_candidates": lnc_candidates,
        "dark_matter_fraction": round(1 - sum(b - a for a, b in coding_spans) / len(s), 4)
        if coding_spans else 1.0,
        "hypotheses": _hypotheses(formatted_clusters, lnc_candidates),
    }


def _hypotheses(clusters: list[dict], lnc: list[dict]) -> list[str]:
    out = []
    for c in clusters:
        out.append(f"Putative enhancer at {c['start']}-{c['end']} with {c['n_motifs']} TF motifs "
                   f"({', '.join(c['tfs'])}): test by reporter assay + CRISPRi of the element.")
    for l in lnc[:3]:
        out.append(f"lncRNA candidate at {l['start']}-{l['end']} ({l['strand']}): "
                   "validate by RT-PCR and subcellular fractionation.")
    return out
