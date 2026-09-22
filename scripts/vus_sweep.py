"""Drop 42: panel-wide VUS splice sweep. Every ClinVar splice variant
classified Uncertain-significance across the 28 golden genes, scored on
the gene's real junction map and carried with its delta - a model-side
prioritization list for VUS reclassification (strong-loss candidates vs
weak/no-perturbation). Same unfiltered-query + description-bucketing
discipline as drop 41 (clinsig [Properties] filters silently drop VUS).

Honest labels: a strong model loss call on a VUS is NOT evidence of
pathogenicity - it is a prioritization signal only; the fixture and the
summary both say so. Variants whose ClinVar-cited c. number lands off the
canonical map (different cited transcript) are counted as unmappable,
not scored.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from sugarcode.modules.deepsplice import variant_at
from validate_multigene_splice import load_gene, GENES as G1, TX_OVERRIDE as T1
import validate_extended_splice as ext
import validate_round3_splice as r3
from validate_gc_donor_golden import _class_bucket

GENES = {"BRCA1": "NG_005905.2", **G1, **ext.GENES, **r3.GENES}
GENES.pop("GJB2", None)  # single-exon CDS; UTR harness owns its variants
TX_OVERRIDE = {**T1, **ext.TX_OVERRIDE, **r3.TX_OVERRIDE}
CDNA_TX = {**ext.CDNA_TX, **r3.CDNA_TX}
WANT = "vus"

PAT = lambda nm, sym: re.compile(
    rf'{nm}\.\d+\({sym}\):c\.(\d+)([+-])(\d+)([ACGT])>([ACGT])')

def main():
    out, summary = {}, {}
    for sym in sorted(GENES):
        if sym in CDNA_TX:
            from sugarcode.bio.splice import cdna_junction_map
            jm = cdna_junction_map(sym, CDNA_TX[sym])
            assert jm["status"] == "ok", (sym, jm["status"])
            donors, acceptors = jm["donors"], jm["acceptors"]
        else:
            donors, acceptors, tx, seq = load_gene(GENES[sym])
            tx = TX_OVERRIDE.get(sym, tx.rsplit(".", 1)[0])
        nm = TX_OVERRIDE.get(sym, tx).rsplit(".", 1)[0]
        ids = entrez.esearch("clinvar",
                             f'{sym}[gene] AND "splice"[All Fields]', retmax=2000)
        docs = {}
        for i in range(0, len(ids), 100):
            docs.update(entrez.esummary("clinvar", ids[i:i+100]))
        pat = PAT(nm, sym)
        cases, unmappable = [], 0
        for doc in docs.values():
            m = pat.search(doc.get("title", ""))
            if not m:
                continue
            germ = doc.get("germline_classification", {})
            desc = germ.get("description", "")
            # "conflicting" is not a _class_bucket value (drop-41 buckets it
            # with pathogenic by description text and labels it via
            # clinvar_sig); here it is its own bucket.
            b = ("conflicting" if desc.startswith("Conflicting")
                 else _class_bucket(desc))
            if b != WANT:
                continue
            n, sign, k = int(m.group(1)), m.group(2), int(m.group(3))
            refb, altb = m.group(4), m.group(5)
            if sign == "+" and k <= 6:
                w, idx, st = donors.get(n), 3 + k - 1, "donor"
            elif sign == "-" and k <= 14:
                w, idx, st = acceptors.get(n), 14 - k, "acceptor"
            else:
                continue
            if not w or w[idx] != refb:
                unmappable += 1
                continue
            res = variant_at(w, idx, altb, st)
            cases.append({"notation": f"c.{n}{sign}{k}{refb}>{altb}",
                          "site_type": st, "window": w, "index": idx,
                          "delta": res["delta"],
                          "site_class": res.get("site_class"),
                          "review": germ.get("review_status", "")})
        strong = [c for c in cases if c["delta"] <= -0.15]
        out[sym] = {"cases": cases, "unmappable": unmappable}
        summary[sym] = {"vus": len(cases), "strong_loss": len(strong),
                        "unmappable": unmappable}
        print(f"{sym:7s} {WANT}={len(cases):4d} strong-loss={len(strong):3d} "
              f"unmappable={unmappable}")
    tot = sum(s["vus"] for s in summary.values())
    tot_strong = sum(s["strong_loss"] for s in summary.values())
    print(f"TOTAL: {tot} {WANT} scored, {tot_strong} with strong loss call "
          f"(prioritization signal, NOT pathogenicity evidence)")
    labels = {"vus": ("VUS", "vus_splice_golden.json",
                        "deltas are model prioritization signals, NOT "
                        "pathogenicity evidence"),
              "conflicting": ("conflicting-classification",
                              "conflicting_splice_golden.json",
                              "ClinVar submitters disagree on these; the model "
                              "delta is on record as ONE computational opinion, "
                              "not a tiebreaker")}
    label, fname, note = labels[WANT]
    json.dump({"source": f"ClinVar live unfiltered sweep 2026-09-22, {label} bucketed on "
                         f"germline description text; {note}",
               "genes": out, "summary": summary},
              open(f"tests/fixtures/{fname}", "w"), indent=1)

if __name__ == "__main__":
    if "--bucket" in sys.argv:
        WANT = sys.argv[sys.argv.index("--bucket") + 1]
    main()
