"""Drop 50: learn the branch-point zone model from the harvest acceptors.
For every GT-AG junction in the 28-gene harvest (recomputed from the same
RefSeqGene CDS spans the junctions.tsv harvest used - validated by matching
the AG-acceptor count), extract the -60..-1 intronic window and find the best
YNYURAY candidate (consensus Y N Y T R A Y, branch A at offset 5, A in
-60..-15). Learns (a) the 7-mer position frequency matrix around the best
candidate's branch A and (b) the branch-A position distribution, pooled over
all acceptors. Harvest-only by discipline (never golden labels).

Writes src/sugarcode/bio/data/splice_sites/branchpoint_pwm.json.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from cryptic_recall_vus import gene_context, GENES

CONS = [set("CT"), set("ACGT"), set("CT"), {"T"}, set("AG"), {"A"}, set("CT")]
PSEUDO = 0.5

def best_candidate(win):
    best = None
    for i in range(len(win) - 6):
        a_pos = -(len(win) - (i + 5))
        if not (-45 <= a_pos <= -18):
            continue
        mer = win[i:i + 7]
        score = sum(b in c for b, c in zip(mer, CONS))
        # tie-break: closest to the empirical branch-A mode (-25, Mercer 2015)
        key = (score, -abs(a_pos + 25))
        if best is None or key > best[1]:
            best = (i, key, mer)
    return best

def main():
    n_ag = 0
    pos_dist = Counter()
    counts = [{b: PSEUDO for b in "ACGT"} for _ in range(7)]
    n_with = 0
    for gene, acc in sorted(GENES.items()):
        seq, strand, spans = gene_context(acc)
        assert strand == 1, f"{gene}: RefSeqGene not in gene orientation"
        for (a, b), (c, d) in zip(spans, spans[1:]):
            if c - 61 < 0:
                continue
            win = seq[c - 61:c - 1]
            if len(win) != 60 or win[58:60] != "AG":
                continue
            n_ag += 1
            bc = best_candidate(win)
            if bc is None:
                continue
            i, score, mer = bc
            n_with += 1
            pos_dist[-(60 - (i + 5))] += 1
            for k, base in enumerate(mer):
                counts[k][base] += 1
    pwm = [{b: round(c[b] / n_with, 6) for b in "ACGT"} for c in counts]
    bg_counts = {b: PSEUDO for b in "ACGT"}
    n_bg = 0
    for gene, acc in sorted(GENES.items()):
        seq, strand, spans = gene_context(acc)
        for (a, b), (c, d) in zip(spans, spans[1:]):
            if c - 61 < 0:
                continue
            win = seq[c - 61:c - 1]
            if len(win) != 60 or win[58:60] != "AG":
                continue
            for base in win[15:42]:  # -45..-18 zone
                bg_counts[base] += 1
                n_bg += 1
    background = {b: round(bg_counts[b] / n_bg, 6) for b in "ACGT"}
    payload = {
        "source": ("best YNYURAY candidate per harvest GT-AG acceptor "
                   f"(-60..-1 intronic window, 28-gene RefSeqGene harvest; "
                   f"{n_with}/{n_ag} acceptors with a candidate; pseudocount "
                   "0.5). Learned 2026-09-22 by scripts/learn_bp_pwm.py. "
                   "Consensus per Mercer et al. 2015 (Genome Res 25:290-303)"),
        "zone": [-45, -18],
        "n_acceptors": n_ag,
        "n_with_candidate": n_with,
        "pwm": pwm,
        "background": background,
        "position_distribution": {str(k): v for k, v in sorted(pos_dist.items())},
    }
    Path("src/sugarcode/bio/data/splice_sites/branchpoint_pwm.json").write_text(
        json.dumps(payload, indent=1))
    print(f"AG acceptors={n_ag} with_candidate={n_with}")
    print("top positions:", pos_dist.most_common(8))
    for k, row in enumerate(pwm):
        print(f"pos{k} ({'YNYTRAY'[k]}):", row)

if __name__ == "__main__":
    main()

