"""Drop 44: learn the polypyrimidine-tract zone model from the harvest
acceptors (junctions.tsv, 1,170 GT-AG junctions, title-verified - the same
set the acceptor PWM is learned from). Position-INDEPENDENT pooled base
frequencies over the tract zone (acceptor window indices 2..11 = c.-12..-3):
the position-specific PWM cannot express 'a purine anywhere in the tract
disrupts it', which the drop-44 groundwork showed is the pathogenic signal
(tract-zone substitutions: pyr-fraction change -0.074 pathogenic vs -0.008
benign, n=72/61).

Writes src/sugarcode/bio/data/splice_sites/acceptor_tract_pwm.json with
pooled frequencies + pseudocount discipline matching the other matrices.
AG-class acceptors only (AT-AC/U12 tracts differ - excluded, documented).
"""
from __future__ import annotations
import json, sys
from pathlib import Path

DATA = Path("src/sugarcode/bio/data/splice_sites")
PSEUDO = 0.5

def main():
    rows = [l.split("\t") for l in (DATA / "junctions.tsv").read_text().splitlines()[1:]]
    acc = [r[4] for r in rows if r[4][12:14] == "AG"]
    counts = {b: PSEUDO for b in "ACGT"}
    n_pos = 0
    for w in acc:
        for b in w[2:12]:
            counts[b] += 1
            n_pos += 1
    freqs = {b: round(counts[b] / n_pos, 6) for b in "ACGT"}
    payload = {
        "source": ("pooled tract-zone (window indices 2..11 = c.-12..-3) base "
                   "frequencies over the harvest AG acceptors (junctions.tsv, "
                   "1,170 GT-AG junctions; pseudocount 0.5). Learned 2026-09-22 "
                   "by scripts/learn_tract_pwm.py"),
        "zone": [2, 12],
        "n_acceptors": len(acc),
        "pwm": freqs,
    }
    (DATA / "acceptor_tract_pwm.json").write_text(json.dumps(payload, indent=1))
    print(f"n_acceptors={len(acc)} zone positions={n_pos}")
    print("tract frequencies:", freqs)
    print("pyrimidine fraction:", round(freqs["C"] + freqs["T"], 4))

if __name__ == "__main__":
    main()
