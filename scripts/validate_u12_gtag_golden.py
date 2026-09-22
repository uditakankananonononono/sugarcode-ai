"""U12 GT-AG golden (drop 31): ClinVar variants at the PTEN intron-1 donor,
the one U2-harvest junction our U12 margin flags - and the intronIC gold
set CONFIRMS it (HomSap-gene-PTEN@rna-NM_001304717.5_2(9), type u12; its
donor window CCTGTATCC matches the junctions.tsv harvest row).

ClinVar cites NM_000314 for PTEN (the record's canonical CDS - the drop-26
pten fixture already runs on it). Pathogenic +1 variants must be called
loss with donor_subtype "U12 GT-AG"; the expert-panel benign c.79+7A>G
must NOT be called loss. Acceptor-side (c.80-k) is documented but U12
acceptor routing was declined in drop 28 - those score on the U2 matrix.
"""
from __future__ import annotations
import json, sys

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from sugarcode.modules.deepsplice import variant_at
from validate_multigene_splice import load_gene

def rows_for(sig_filter):
    # no clinsig property filter: it excludes the "Likely ..." tiers, which
    # are exactly where these variants sit. Classify on the description text.
    ids = entrez.esearch("clinvar",
                         'PTEN[gene] AND "splice"[All Fields]', retmax=500)
    docs = entrez.esummary("clinvar", ids)
    import re
    pat = re.compile(r"NM_000314\.\d+\(PTEN\):c\.(79\+|80-)(\d+)([ACGT])>([ACGT])")
    rows = []
    for uid, doc in docs.items():
        m = pat.search(doc.get("title", ""))
        if not m: continue
        germ = doc.get("germline_classification", {})
        desc = (germ.get("description", "") or "").lower()
        if "conflicting" in desc or "uncertain" in desc or not desc:
            continue
        if sig_filter == "pathogenic" and "pathogenic" in desc:
            pass
        elif sig_filter == "benign" and "benign" in desc and "pathogenic" not in desc:
            pass
        else:
            continue
        rows.append({"uid": uid, "sig": germ.get("description", ""),
                     "review": germ.get("review_status", ""),
                     "site": m.group(1), "k": int(m.group(2)),
                     "ref": m.group(3), "alt": m.group(4)})
    return rows

def main():
    donors, acceptors, tx, seq = load_gene("NG_007466.2")
    assert donors.get(79) == "CCTGTATCC", donors.get(79)
    cases = []
    for sig_filter, cls in (("pathogenic", "pathogenic"), ("benign", "benign")):
        for r in rows_for(sig_filter):
            if r["site"] == "79+" and r["k"] <= 6:
                w, idx, st = donors[79], 3 + r["k"] - 1, "donor"
            elif r["site"] == "80-" and r["k"] <= 14:
                w, idx, st = acceptors[80], 14 - r["k"], "acceptor"
            else:
                continue
            if w[idx] != r["ref"]:
                continue
            res = variant_at(w, idx, r["alt"], st)
            cases.append({"notation": f"c.{r['site']}{r['k']}{r['ref']}>{r['alt']}",
                          "site_type": st, "window": w, "index": idx,
                          "delta": res["delta"],
                          "donor_subtype": res.get("donor_subtype"),
                          "sig": cls, "clinvar_sig": r["sig"], "review": r["review"],
                          "consequence": res["consequence"]})
    json.dump({"source": "ClinVar live query 2026-09-22 (PTEN NM_000314, c.79+/c.80- "
                         "splice variants) + RefSeqGene NG_007466.2 windows; PTEN intron 1 "
                         "confirmed U12 GT-AG by the intronIC gold set "
                         "(HomSap-gene-PTEN@rna-NM_001304717.5_2(9))",
               "cases": cases},
              open("tests/fixtures/pten_u12_gtag_golden.json", "w"), indent=1)
    for c in sorted(cases, key=lambda c: c["notation"]):
        print(f'{c["notation"]:16s} {c["sig"]:10s} {c["clinvar_sig"]:22s} '
              f'delta={c["delta"]:+.3f} subtype={c["donor_subtype"]} [{c["review"][:30]}]')

if __name__ == "__main__":
    main()
