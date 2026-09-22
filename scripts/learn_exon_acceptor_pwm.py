"""Drop 51: learn the acceptor-side EXONIC +1..+3 position model from the
longest-CDS harvest acceptors (the same 646-acceptor set as drop 50's
branch-point model - documented subset of the 1,170 all-isoform harvest).
The calibrated 15-mer acceptor matrix carries only the +1 exonic base; this
separate matrix extends the exonic side to +2/+3 so ClinVar coding
substitutions at the first three bases of acceptor exons can be scored
without touching the calibrated window. Background: pooled base frequencies
over the first 30 coding bases of the same downstream exons.
Writes src/sugarcode/bio/data/splice_sites/acceptor_exon_pwm.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from cryptic_recall_vus import gene_context, GENES

PSEUDO = 0.5

def main():
    counts = [{b: PSEUDO for b in "ACGT"} for _ in range(3)]
    bg = {b: PSEUDO for b in "ACGT"}
    n_acc, n_bg = 0, 0
    for gene, acc in sorted(GENES.items()):
        seq, strand, spans = gene_context(acc)
        assert strand == 1
        for (a, b), (c, d) in zip(spans, spans[1:]):
            if c - 61 < 0:
                continue
            win = seq[c - 61:c - 1]
            if len(win) != 60 or win[58:60] != "AG":
                continue
            exon = seq[c - 1:d]  # 1-based c..d inclusive
            if len(exon) < 30:
                continue
            n_acc += 1
            for k in range(3):
                counts[k][exon[k]] += 1
            for base in exon[:30]:
                bg[base] += 1
                n_bg += 1
    pwm = [{b: round(c[b] / n_acc, 6) for b in "ACGT"} for c in counts]
    background = {b: round(bg[b] / n_bg, 6) for b in "ACGT"}
    payload = {
        "source": ("acceptor-side exonic +1..+3 base frequencies over the "
                   "646 longest-CDS harvest GT-AG acceptors (same set as "
                   "branchpoint_pwm.json; background pooled over the first 30 "
                   "coding bases of the downstream exons; pseudocount 0.5). "
                   "Learned 2026-09-22 by scripts/learn_exon_acceptor_pwm.py"),
        "n_acceptors": n_acc,
        "pwm": pwm,
        "background": background,
    }
    Path("src/sugarcode/bio/data/splice_sites/acceptor_exon_pwm.json").write_text(
        json.dumps(payload, indent=1))
    print(f"acceptors={n_acc}")
    for k, row in enumerate(pwm):
        print(f"+{k+1}:", row)
    print("bg:", background)

if __name__ == "__main__":
    main()
