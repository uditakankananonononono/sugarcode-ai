"""Drop 51: exonic acceptor +1..+3 sweep. Drop 47 harvested ClinVar coding
substitutions at the FIRST coding base of acceptor exons (216 cases); this
extends to +2/+3, scoring each with the harvest-learned acceptor_exon_pwm
(log-odds vs first-30-coding-base background; learned offline, no golden
fit). Same unfiltered ClinVar sweep + germline-description bucketing as
every prior sweep (drop-41 discipline). Exonic acceptor positions are
codon-constrained (+3 mostly wobble), so a weak/flat result is a legitimate
honest outcome.
Writes tests/fixtures/exonic_acceptor3_golden.json.
"""
from __future__ import annotations
import json, math, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from cryptic_recall_vus import gene_context, GENES
from validate_multigene_splice import TX_OVERRIDE as T1
import validate_extended_splice as ext
import validate_round3_splice as r3
from validate_gc_donor_golden import _class_bucket

TX_OVERRIDE = {**T1, **ext.TX_OVERRIDE, **r3.TX_OVERRIDE}
EP = json.loads(Path("src/sugarcode/bio/data/splice_sites/acceptor_exon_pwm.json").read_text())

def lo(pos, base):
    return math.log2(EP["pwm"][pos][base] / EP["background"][base])

def main():
    import os
    only = set(os.environ.get("SWEEP_GENES", "").split(",")) - {""}
    out, summary = {}, {}
    for sym in sorted(GENES):
        if only and sym not in only:
            continue
        seq, strand, spans = gene_context(GENES[sym])
        # cDNA N of each acceptor's first coding base + exonic triplet
        acc3 = {}
        n = 0
        for a, b in spans:
            if n:
                acc3[n + 1] = seq[a - 1:a + 2]  # triplet +1..+3
            n += b - a + 1
        ids = entrez.esearch("clinvar",
                             f'{sym}[gene] AND "splice"[All Fields]', retmax=2000)
        docs = {}
        for i in range(0, len(ids), 100):
            docs.update(entrez.esummary("clinvar", ids[i:i+100]))
        # loose accession match; cDNA validity enforced by the per-variant
        # ref-base check against the harvest exon map below
        pats = [re.compile(rf'\({sym}\):c\.(\d+)([ACGT])>([ACGT])')]
        cases = []
        for doc in docs.values():
            title = doc.get("title", "")
            m = next((p.search(title) for p in pats if p.search(title)), None)
            if not m:
                continue
            pos, refb, altb = int(m.group(1)), m.group(2), m.group(3)
            for N, tri in acc3.items():
                if N <= pos <= N + 2 and len(tri) == 3 and tri[pos - N] == refb:
                    germ = doc.get("germline_classification", {})
                    desc = germ.get("description", "")
                    b = ("conflicting" if desc.startswith("Conflicting")
                         else _class_bucket(desc))
                    cases.append({
                        "notation": f"c.{pos}{refb}>{altb}",
                        "exonic_offset": pos - N + 1,  # +1..+3
                        "ref_triplet": tri,
                        "delta": round(lo(pos - N, altb) - lo(pos - N, refb), 4),
                        "sig": b, "clinvar_sig": desc,
                        "review": germ.get("review_status", "")})
                    break
        out[sym] = {"cases": cases}
        summary[sym] = {"n": len(cases), "buckets": dict(Counter(c["sig"] for c in cases))}
        print(f"{sym:7s} n={len(cases):3d} {summary[sym]['buckets']}")
    tot = sum(s["n"] for s in summary.values())
    print(f"TOTAL: {tot} exonic acceptor +1..+3 variants")
    for sig in ("pathogenic", "benign", "vus", "conflicting"):
        ds = [c["delta"] for g in out.values() for c in g["cases"] if c["sig"] == sig]
        if ds:
            print(f"{sig:12s} n={len(ds):4d} mean_delta={sum(ds)/len(ds):+.4f} "
                  f"frac<=-0.5: {sum(d <= -0.5 for d in ds)/len(ds):.3f}")
    by_off = {}
    for g in out.values():
        for c in g["cases"]:
            by_off.setdefault(c["exonic_offset"], []).append(c)
    for off in (1, 2, 3):
        grp = by_off.get(off, [])
        p = [c["delta"] for c in grp if c["sig"] == "pathogenic"]
        print(f"offset +{off}: n={len(grp)} pathogenic n={len(p)} "
              f"mean={sum(p)/len(p):+.4f}" if p else f"offset +{off}: n={len(grp)}")
    if only:
        for sym, g in out.items():
            json.dump(g, open(f"/tmp/sweep51_{sym}.json", "w"), indent=1)
        return
    json.dump({"source": "ClinVar live unfiltered sweep 2026-09-22: coding "
                         "substitutions at +1..+3 of acceptor exons, scored with "
                         "acceptor_exon_pwm (harvest-learned, offline)",
               "genes": out, "summary": summary},
              open("tests/fixtures/exonic_acceptor3_golden.json", "w"), indent=1)

if __name__ == "__main__":
    main()

