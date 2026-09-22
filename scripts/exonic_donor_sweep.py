"""Drop 45: exonic donor-window sweep. ClinVar cites exonic splice-region
variants as CODING substitutions (c.NX>Y, no +/- offset) - the splice
goldens' donor cases are all intronic (c.N+k), so the exonic -3..-1 donor
positions have never been harvested. For every gene, the donor key c.N IS
the terminal coding base of the exon: c.N -> window index 2 (-1),
c.N-1 -> index 1 (-2), c.N-2 -> index 0 (-3). This sweep collects every
ClinVar variant cited at those positions (all classifications, unfiltered
query + germline-description bucketing - the drop-41 discipline) and
scores it with variant_at on the real junction map.

Honest note: 'splice'[All Fields] catches variants whose ClinVar record
mentions splice; a coding variant with splice effect recorded only as
missense/nonsense is out of scope - counted as not-harvestable, not hidden.
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
GENES.pop("GJB2", None)
TX_OVERRIDE = {**T1, **ext.TX_OVERRIDE, **r3.TX_OVERRIDE}
CDNA_TX = {**ext.CDNA_TX, **r3.CDNA_TX}

def main():
    out, summary = {}, {}
    for sym in sorted(GENES):
        if sym in CDNA_TX:
            from sugarcode.bio.splice import cdna_junction_map
            jm = cdna_junction_map(sym, CDNA_TX[sym])
            assert jm["status"] == "ok", (sym, jm["status"])
            donors = jm["donors"]
        else:
            donors, acceptors, tx, seq = load_gene(GENES[sym])
            tx = TX_OVERRIDE.get(sym, tx.rsplit(".", 1)[0])
        nm = TX_OVERRIDE.get(sym, tx).rsplit(".", 1)[0]
        ids = entrez.esearch("clinvar",
                             f'{sym}[gene] AND "splice"[All Fields]', retmax=2000)
        docs = {}
        for i in range(0, len(ids), 100):
            docs.update(entrez.esummary("clinvar", ids[i:i+100]))
        pat = re.compile(rf'{nm}\.\d+\({sym}\):c\.(\d+)([ACGT])>([ACGT])')
        cases = []
        for doc in docs.values():
            m = pat.search(doc.get("title", ""))
            if not m:
                continue
            n, refb, altb = int(m.group(1)), m.group(2), m.group(3)
            # exonic -1/-2/-3 relative to a donor at c.N
            for N, w in donors.items():
                idx = 2 - (N - n)
                if 0 <= idx <= 2 and w[idx] == refb:
                    germ = doc.get("germline_classification", {})
                    desc = germ.get("description", "")
                    b = ("conflicting" if desc.startswith("Conflicting")
                         else _class_bucket(desc))
                    res = variant_at(w, idx, altb, "donor")
                    cases.append({"notation": f"c.{n}{refb}>{altb}",
                                  "exonic_offset": idx - 3,  # true position: -1 terminal
                                  "site_type": "donor", "window": w,
                                  "index": idx, "delta": res["delta"],
                                  "site_class": res.get("site_class"),
                                  "sig": b, "clinvar_sig": desc,
                                  "review": germ.get("review_status", "")})
                    break
        out[sym] = {"cases": cases}
        buckets = {}
        for c in cases:
            buckets[c["sig"]] = buckets.get(c["sig"], 0) + 1
        summary[sym] = {"exonic_cases": len(cases), "buckets": buckets}
        print(f"{sym:7s} exonic={len(cases):3d} {buckets}")
    tot = sum(s["exonic_cases"] for s in summary.values())
    print(f"TOTAL: {tot} exonic donor-window variants harvested")
    json.dump({"source": "ClinVar live unfiltered sweep 2026-09-22: variants cited as "
                         "coding substitutions (c.NX>Y) at exon-terminal -1/-2/-3 donor "
                         "positions, bucketed on germline description text",
               "genes": out, "summary": summary},
              open("tests/fixtures/exonic_donor_golden.json", "w"), indent=1)

if __name__ == "__main__":
    main()
