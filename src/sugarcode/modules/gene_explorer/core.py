from __future__ import annotations
from ...bio.sequence import (
    clean_dna, transcribe, translate, gc_content, molecular_weight,
    hydrophobicity_profile, AA_NAMES, orfs,
)


def _segments(dna: str, n: int = 6) -> list[dict]:
    """Split the gene into n labelled sequence segments for UI display."""
    dna = clean_dna(dna)
    n = max(1, min(n, len(dna)))
    size = len(dna) // n
    segs = []
    for i in range(n):
        start = i * size
        end = len(dna) if i == n - 1 else (i + 1) * size
        segs.append({"index": i, "start": start, "end": end,
                     "sequence": dna[start:end], "gc": round(gc_content(dna[start:end]), 4)})
    return segs


def explore(dna: str, gene_name: str = "gene", reading_frame: int = 0) -> dict:
    """Full central-dogma trace for a DNA sequence.

    Returns DNA stats, the mRNA transcript, the translated protein with
    annotations, detected ORFs and display segments.
    """
    dna = clean_dna(dna)
    mrna = transcribe(dna)
    protein = translate(dna, reading_frame=reading_frame)
    mature = protein.split("*")[0]
    found_orfs = orfs(dna, min_aa=10)
    longest = max(found_orfs, key=lambda o: o["aa_length"], default=None)
    return {
        "gene": gene_name,
        "dna": {
            "length": len(dna),
            "gc_content": round(gc_content(dna), 4),
            "sequence": dna,
            "segments": _segments(dna),
        },
        "mrna": {
            "length": len(mrna),
            "sequence": mrna,
            "codon_count": len(mrna) // 3,
        },
        "protein": {
            "length": len(mature),
            "sequence": mature,
            "molecular_weight_da": round(molecular_weight(mature), 2),
            "hydrophobicity": [round(v, 3) for v in hydrophobicity_profile(mature)],
            "composition": {aa: mature.count(aa) for aa in sorted(set(mature)) if aa in AA_NAMES},
            "truncated_by_stop": "*" in protein,
        },
        "orfs": [
            {"strand": o["strand"], "frame": o["frame"], "start": o["start"],
             "end": o["end"], "aa_length": o["aa_length"]}
            for o in found_orfs
        ],
        "longest_orf": ({k: longest[k] for k in ("strand", "frame", "start", "end", "aa_length")}
                        if longest else None),
        "animation_script": _animation_steps(dna, mrna, mature),
    }


def _animation_steps(dna: str, mrna: str, protein: str) -> list[dict]:
    """Keyframe descriptions for a 3D central-dogma animation."""
    return [
        {"step": 1, "scene": "unwind", "detail": f"DNA double helix ({len(dna)} bp) unwinds; strands separate."},
        {"step": 2, "scene": "transcribe", "detail": f"RNA polymerase builds {len(mrna)} nt pre-mRNA 5'->3'."},
        {"step": 3, "scene": "process", "detail": "5' cap added, poly-A tail appended, introns spliced out."},
        {"step": 4, "scene": "translate", "detail": f"Ribosome scans to AUG; tRNAs elongate a {len(protein)} aa chain."},
        {"step": 5, "scene": "fold", "detail": "Chain folds into secondary/tertiary structure; chaperones assist."},
    ]


def central_dogma_report(dna: str, gene_name: str = "gene") -> str:
    r = explore(dna, gene_name)
    lines = [
        f"Gene Explorer report: {gene_name}",
        f"DNA: {r['dna']['length']} bp, GC {r['dna']['gc_content']:.1%}",
        f"mRNA: {r['mrna']['length']} nt, {r['mrna']['codon_count']} codons",
        f"Protein: {r['protein']['length']} aa, {r['protein']['molecular_weight_da']} Da",
    ]
    if r["protein"]["truncated_by_stop"]:
        lines.append("Note: internal stop codon - protein shown up to first stop.")
    if r["longest_orf"]:
        o = r["longest_orf"]
        lines.append(f"Longest ORF: strand {o['strand']} frame {o['frame']} "
                     f"({o['aa_length']} aa) at {o['start']}..{o['end']}")
    return "\n".join(lines)
