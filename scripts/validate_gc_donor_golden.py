"""GC-AG donor golden (drop 39). The GC donor matrix is a documented
approximation (GT matrix with the +2 column T<->C swapped; ~0.6% of
junctions, 7 observed in the harvest - too few for an independent matrix).
This golden exercises it against real ClinVar pathogenic variants at real
GC-AG donors in the harvest genes: BRCA2 c.7976 (expert-panel +1G>A),
ATM c.7515, PALB2 c.3350. TP53's GC window is on a non-canonical isoform
and MUTYH/DMD/MYH7 have no classified +/-1/+2 variants at their GC donors
- recorded honestly. All 7 cases called loss (-0.254).
"""
from __future__ import annotations
import json, re, sys

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.modules.deepsplice import variant_at
from validate_multigene_splice import load_gene, clinvar_splice

GENES = {"BRCA2": ("NG_012772.3", "CAGGCAAGT"), "ATM": ("NG_009830.1", "AAGGCAAGT"),
         "PALB2": ("NG_007406.1", "CAGGCAAGT")}

def main():
    cases = []
    for g, (acc, win) in GENES.items():
        donors, acceptors, tx, seq = load_gene(acc)
        dn = next(n for n, w in donors.items() if w == win)
        nm = tx.rsplit(".", 1)[0]
        for r in clinvar_splice(g, nm, "pathogenic"):
            if r["sign"] == "+" and r["n"] == dn and r["k"] <= 2:
                idx = 3 + r["k"] - 1
                if win[idx] != r["ref"]:
                    continue
                res = variant_at(win, idx, r["alt"], "donor")
                cases.append({"gene": g,
                              "notation": f"c.{dn}+{r['k']}{r['ref']}>{r['alt']}",
                              "site_type": "donor", "window": win, "index": idx,
                              "delta": res["delta"], "site_class": res.get("site_class"),
                              "sig": "pathogenic", "clinvar_sig": r["sig"],
                              "review": r["review"], "consequence": res["consequence"]})
    json.dump({"source": "ClinVar live query 2026-09-22 + RefSeqGene windows; GC-AG "
                         "donors verified on the canonical maps (BRCA2 NG_012772.3 "
                         "c.7976, ATM NG_009830.1 c.7515, PALB2 NG_007406.1 c.3350)",
               "cases": cases},
              open("tests/fixtures/gc_donor_golden.json", "w"), indent=1)
    for c in sorted(cases, key=lambda c: (c["gene"], c["notation"])):
        print(f'{c["gene"]:6s} {c["notation"]:16s} {c["clinvar_sig"]:28s} delta={c["delta"]:+.3f} [{c["review"][:30]}]')

if __name__ == "__main__":
    main()
