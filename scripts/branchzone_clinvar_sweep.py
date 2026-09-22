"""Drop 52: branch-zone ClinVar sweep. The Leman functional set gave only
n=8 covered functional variants (drop 50), too small for a specificity
claim. This sweep enlarges the test with ClinVar-classified intronic
substitutions at c.-15..-50 relative to natural acceptors across the 28
harvest genes (unfiltered query + germline-description bucketing, drop-41
discipline; same query text as drop 51 so the live docs come from cache).
Each variant is mapped into the -60..-1 intronic window with a per-variant
ref-base check (mismatches loudly excluded), then scored with the drop-50
harvest-learned branchpoint_pwm (best-candidate log-odds, zone -45..-18;
harvest-learned, no golden fit). Also records the tract-zone (-12..-3)
overlap so BP-zone (-45..-18) and tract effects stay separable.
Writes tests/fixtures/branchzone_clinvar_golden.json.
"""
from __future__ import annotations
import json, math, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from cryptic_recall_vus import gene_context, GENES
from validate_gc_donor_golden import _class_bucket

BP = json.loads(Path("src/sugarcode/bio/data/splice_sites/branchpoint_pwm.json").read_text())
ZONE = (-45, -18)

def pwm_score(mer):
    return sum(math.log2(BP["pwm"][k][b] / BP["background"][b])
               for k, b in enumerate(mer))

def best_pwm(win):
    best = None
    for i in range(len(win) - 6):
        a_pos = -(len(win) - (i + 5))
        if not (ZONE[0] <= a_pos <= ZONE[1]):
            continue
        s = pwm_score(win[i:i + 7])
        if best is None or s > best:
            best = s
    return best if best is not None else 0.0

def main():
    out, summary = {}, {}
    for sym in sorted(GENES):
        seq, strand, spans = gene_context(GENES[sym])
        # cDNA N of each acceptor's first coding base -> -60..-1 window
        acc = {}
        n = 0
        for a, b in spans:
            if n:
                w0 = a - 61
                if w0 >= 0:
                    acc[n + 1] = seq[a - 61:a - 1]
            n += b - a + 1
        ids = entrez.esearch("clinvar",
                             f'{sym}[gene] AND "splice"[All Fields]', retmax=2000)
        docs = {}
        for i in range(0, len(ids), 100):
            docs.update(entrez.esummary("clinvar", ids[i:i+100]))
        pat = re.compile(rf'\({sym}\):c\.(\d+)-(\d+)([ACGT])>([ACGT])')
        cases, excluded = [], []
        for doc in docs.values():
            m = pat.search(doc.get("title", ""))
            if not m:
                continue
            cn, d, refb, altb = int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)
            if not (3 <= d <= 50) or cn not in acc:
                continue
            win = acc[cn]
            if len(win) != 60:
                continue
            idx = 60 - d
            if win[idx] != refb:
                excluded.append(f"c.{cn}-{d}{refb}>{altb}")
                continue
            alt_win = win[:idx] + altb + win[idx + 1:]
            germ = doc.get("germline_classification", {})
            desc = germ.get("description", "")
            b = ("conflicting" if desc.startswith("Conflicting")
                 else _class_bucket(desc))
            cases.append({
                "notation": f"c.{cn}-{d}{refb}>{altb}", "dist": d,
                "in_bp_zone": ZONE[0] <= -d <= ZONE[1],
                "in_tract_zone": 3 <= d <= 12,
                "bp_pwm_drop": round(best_pwm(win) - best_pwm(alt_win), 4),
                "sig": b, "clinvar_sig": desc,
                "review": germ.get("review_status", "")})
        out[sym] = {"cases": cases, "excluded_refmismatch": excluded}
        summary[sym] = {"n": len(cases), "excluded": len(excluded),
                        "buckets": dict(Counter(c["sig"] for c in cases))}
        print(f"{sym:7s} n={len(cases):3d} excl={len(excluded)} {summary[sym]['buckets']}")
    allc = [c for g in out.values() for c in g["cases"]]
    print(f"TOTAL: {len(allc)} branch-zone-window variants "
          f"(excluded ref-mismatch: {sum(s['excluded'] for s in summary.values())})")
    bpz = [c for c in allc if c["in_bp_zone"]]
    print(f"BP-zone (-45..-18): n={len(bpz)}")
    for sig in ("pathogenic", "benign", "vus", "conflicting"):
        ds = [c["bp_pwm_drop"] for c in bpz if c["sig"] == sig]
        if ds:
            print(f"  {sig:12s} n={len(ds):3d} mean_drop={sum(ds)/len(ds):+.4f} "
                  f"frac>=0.5: {sum(d >= 0.5 for d in ds)/len(ds):.3f}")
    json.dump({"source": "ClinVar live unfiltered sweep 2026-09-22: intronic "
                         "substitutions c.-3..-50 at natural acceptors (28 genes), "
                         "ref-base verified, scored with branchpoint_pwm",
               "genes": out, "summary": summary},
              open("tests/fixtures/branchzone_clinvar_golden.json", "w"), indent=1)

if __name__ == "__main__":
    main()
