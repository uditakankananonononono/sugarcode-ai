"""Groundwork for the tract-scoring candidate (analysis only - no model
change). Question: does the polypyrimidine tract (acceptor window indices
2..11 = c.-12..-3) separate pathogenic from benign acceptor variants in the
golden fixtures? Pure analysis over hermetic fixtures, no network.

Findings (2026-09-22, 28-gene fixtures):
- acceptor -3..-14 cases: 79 pathogenic / 72 benign
- pathogenic tract-zone substitutions reduce tract pyrimidine content
  (mean -0.074 vs -0.008 benign) and shorten the longest T-run
  (-0.15 vs +0.15 benign)
- the current AG-only matrix already separates them weakly
  (mean delta -0.057 pathogenic vs -0.002 benign) - a tract term could add
  discrimination in exactly the zone the matrix ignores.
Next step (next drop): learn a tract term from the harvest acceptor
windows, re-run pooled stats, regression-lock canonical capture.
"""
import json, re, statistics as st
from pathlib import Path


def tract(win):
    zone = win[2:12]
    pyr = sum(1 for b in zone if b in "CT")
    longest, run = 0, 0
    for b in zone:
        run = run + 1 if b == "T" else 0
        longest = max(longest, run)
    return pyr / len(zone), longest


def main():
    rows = []
    for f in sorted(Path("tests/fixtures").glob("*_splice_golden.json")):
        d = json.loads(f.read_text())
        for sig in ("pathogenic", "benign"):
            for c in d.get(sig, []):
                if c["site_type"] != "acceptor":
                    continue
                m = re.search(r"-(\d+)([ACGT])>([ACGT])", c["notation"])
                k = int(m.group(1))
                if not (3 <= k <= 12):
                    continue
                idx = 14 - k
                if not (2 <= idx <= 11):
                    continue
                alt = m.group(3)
                alt_win = c["window"][:idx] + alt + c["window"][idx+1:]
                rows.append((sig,
                             tract(alt_win)[0] - tract(c["window"])[0],
                             tract(alt_win)[1] - tract(c["window"])[1],
                             c["delta"]))
    for sig in ("pathogenic", "benign"):
        r = [x for x in rows if x[0] == sig]
        print(f"{sig}: n={len(r)} tract-pyr change {st.mean(x[1] for x in r):+.3f} "
              f"T-run change {st.mean(x[2] for x in r):+.2f} "
              f"model delta {st.mean(x[3] for x in r):+.3f}")


if __name__ == "__main__":
    main()

