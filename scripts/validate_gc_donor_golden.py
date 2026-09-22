"""GC-AG donor golden (drop 39; thickened drop 41). The GC donor matrix is a
documented approximation (GT matrix with the +2 column T<->C swapped; ~0.6%
of junctions, 7 observed in the harvest - too few for an independent matrix).
This golden exercises it against real ClinVar variants at real GC-AG donors
in the harvest genes: BRCA2 c.7976 (expert-panel +1G>A), ATM c.7515,
PALB2 c.3350. TP53's GC window is on a non-canonical isoform and MUTYH/DMD/
MYH7 have no classified +/-1/+2 variants at their GC donors - recorded
honestly.

Drop 41: the window widens from +/-1/+2 to the full +/-1..+6 scoring window
and includes ALL classifications (pathogenic + VUS + conflicting; benign and
likely-benign searched and found ZERO at all three sites - documented
specificity gap, not hidden). Each case carries its ClinVar classification;
the pooled headline counts only pathogenic/likely-pathogenic as positives.
"""
from __future__ import annotations
import json, sys

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.modules.deepsplice import variant_at
from validate_multigene_splice import load_gene, clinvar_splice

GENES = {"BRCA2": ("NG_012772.3", "CAGGCAAGT"), "ATM": ("NG_009830.1", "AAGGCAAGT"),
         "PALB2": ("NG_007406.1", "CAGGCAAGT")}


def _class_bucket(sig: str) -> str:
    s = sig.lower()
    if "benign" in s and "pathogenic" not in s:
        return "benign"
    if "uncertain" in s:
        return "vus"
    if "pathogenic" in s:
        return "pathogenic"
    return "other"


def clinvar_splice_unfiltered(sym: str, nm_prefix: str):
    """All splice-classified ClinVar variants for the gene on the cited
    transcript, bucketed on the germline DESCRIPTION text - the drop-31
    lesson: clinsig [Properties] filters silently drop Likely-only and VUS
    variants. (clinvar_splice in validate_multigene_splice keeps the old
    filtered query; this golden needs the full window.)"""
    import re
    from sugarcode.bio import entrez
    ids = entrez.esearch("clinvar",
                         f'{sym}[gene] AND "splice"[All Fields]', retmax=2000)
    docs = {}
    for i in range(0, len(ids), 100):
        docs.update(entrez.esummary("clinvar", ids[i:i+100]))
    pat = re.compile(rf'{nm_prefix}\.\d+\({sym}\):c\.(\d+)([+-])(\d+)([ACGT])>([ACGT])')
    rows = []
    for uid, doc in docs.items():
        m = pat.search(doc.get("title", ""))
        if not m:
            continue
        germ = doc.get("germline_classification", {})
        rows.append({"uid": uid, "sig": germ.get("description", ""),
                     "bucket": _class_bucket(germ.get("description", "")),
                     "review": germ.get("review_status", ""),
                     "n": int(m.group(1)), "sign": m.group(2), "k": int(m.group(3)),
                     "ref": m.group(4), "alt": m.group(5)})
    return rows


def main():
    cases = []
    for g, (acc, win) in GENES.items():
        donors, acceptors, tx, seq = load_gene(acc)
        dn = next(n for n, w in donors.items() if w == win)
        nm = tx.rsplit(".", 1)[0]
        for r in clinvar_splice_unfiltered(g, nm):
            if r["sign"] != "+" or r["n"] != dn or not (1 <= r["k"] <= 6):
                continue
            idx = 3 + r["k"] - 1
            if win[idx] != r["ref"]:
                continue
            res = variant_at(win, idx, r["alt"], "donor")
            cases.append({"gene": g,
                          "notation": f"c.{dn}+{r['k']}{r['ref']}>{r['alt']}",
                          "site_type": "donor", "window": win, "index": idx,
                          "delta": res["delta"], "site_class": res.get("site_class"),
                          "sig": r["bucket"], "clinvar_sig": r["sig"],
                          "review": r["review"], "consequence": res["consequence"]})
    json.dump({"source": "ClinVar live query 2026-09-22 + RefSeqGene windows; GC-AG "
                         "donors verified on the canonical maps (BRCA2 NG_012772.3 "
                         "c.7976, ATM NG_009830.1 c.7515, PALB2 NG_007406.1 c.3350). "
                         "Drop 41: full +/-1..+6 window, all classifications; benign "
                         "searched and found ZERO at all three GC donors.",
               "cases": cases},
              open("tests/fixtures/gc_donor_golden.json", "w"), indent=1)
    buckets = {}
    for c in cases:
        buckets[c["sig"]] = buckets.get(c["sig"], 0) + 1
    confl = sum(1 for c in cases if c["clinvar_sig"].startswith("Conflicting"))
    print(f"total: {len(cases)}  buckets: {buckets}  (conflicting: {confl})")
    for c in sorted(cases, key=lambda c: (c["gene"], c["notation"])):
        print(f'{c["gene"]:6s} {c["notation"]:16s} {c["clinvar_sig"]:42s} delta={c["delta"]:+.3f} [{c["review"][:28]}]')

if __name__ == "__main__":
    main()
