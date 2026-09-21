"""Live golden validation: deepsplice PWM vs ClinVar BRCA1 splice variants.

Maps ClinVar NM_007294 splice-SNPs onto RefSeqGene NG_005905.2 junction
windows, scores ref vs alt with the learned PWM, and reports direction
accuracy. Writes the fixture used by the hermetic regression test.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from sugarcode.modules.deepsplice import variant_at, score_donor, score_acceptor
from gb_parse import parse_genbank, transcript_exons

PAT = re.compile(r'NM_007294\.\d+\(BRCA1\):c\.(\d+)([+-])(\d+)([ACGT])>([ACGT])')

def load_brca1():
    txt = entrez._get("efetch.fcgi", {"db": "nuccore", "id": "NG_005905.2",
                                      "rettype": "gb", "retmode": "text"}).decode()
    gb = parse_genbank(txt); seq = gb["sequence"]
    mrna = [f for f in gb["features"] if f["key"] == "mRNA" and len(f["spans"]) == 23
            and f["strand"] == 1][0]
    cds = [f for f in gb["features"] if f["key"] == "CDS" and f["strand"] == 1
           and f["spans"][0][0] > 92000][0]
    cds_spans = transcript_exons(cds)
    def cdna_of(pos):
        n = 0
        for a, b in cds_spans:
            if pos < a: return None
            if a <= pos <= b: return n + (pos - a + 1)
            n += b - a + 1
        return None
    exons = transcript_exons(mrna)
    donors, acceptors = {}, {}
    for (a, b), (c, d) in zip(exons, exons[1:]):
        dn, ac = cdna_of(b), cdna_of(c)
        if dn: donors[dn] = seq[b-3:b+6]
        if ac: acceptors[ac] = seq[c-15:c]
    return donors, acceptors

def clinvar_splice(term):
    ids = entrez.esearch("clinvar", term, retmax=1000)
    docs = {}
    for i in range(0, len(ids), 100):
        docs.update(entrez.esummary("clinvar", ids[i:i+100]))
    rows = []
    for uid, doc in docs.items():
        m = PAT.search(doc.get("title", ""))
        if not m: continue
        germ = doc.get("germline_classification", {})
        rows.append({"uid": uid, "sig": germ.get("description", ""),
                     "review": germ.get("review_status", ""),
                     "n": int(m.group(1)), "sign": m.group(2), "k": int(m.group(3)),
                     "ref": m.group(4), "alt": m.group(5)})
    return rows

def build_cases(rows, donors, acceptors, cls):
    cases, skipped = [], []
    for r in rows:
        if r["sign"] == "+" and r["k"] <= 6:
            w = donors.get(r["n"]); idx = 3 + r["k"] - 1; st = "donor"
        elif r["sign"] == "-" and r["k"] <= 14:
            w = acceptors.get(r["n"]); idx = 14 - r["k"]; st = "acceptor"
        else:
            continue
        if not w:
            skipped.append(r); continue
        if w[idx] != r["ref"]:
            skipped.append({**r, "reason": f"ref mismatch: window has {w[idx]}"}); continue
        res = variant_at(w, idx, r["alt"], st)
        cases.append({"notation": f"c.{r['n']}{r['sign']}{r['k']}{r['ref']}>{r['alt']}",
                      "site_type": st, "window": w, "index": idx,
                      "ref_score": res["ref_score"], "alt_score": res["alt_score"],
                      "delta": res["delta"], "sig": cls, "review": r["review"],
                      "consequence": res["consequence"]})
    return cases, skipped

def main():
    donors, acceptors = load_brca1()
    path = clinvar_splice('BRCA1[gene] AND "splice"[All Fields] AND "clinsig pathogenic"[Properties]')
    ben = clinvar_splice('BRCA1[gene] AND "splice"[All Fields] AND "clinsig benign"[Properties]')
    pc, pskip = build_cases(path, donors, acceptors, "pathogenic")
    bc, bskip = build_cases(ben, donors, acceptors, "benign")
    print(f"pathogenic cases: {len(pc)} (skipped {len(pskip)}); benign cases: {len(bc)} (skipped {len(bskip)})")
    for s in pskip[:10]: print("  skip:", s.get("reason", "outside window"), s)
    def summ(cases, label):
        for cutoff in (-0.30, -0.10):
            n = sum(1 for c in cases if c["delta"] <= cutoff)
            print(f"{label}: delta <= {cutoff}: {n}/{len(cases)} ({100*n/len(cases):.0f}%)")
    summ(pc, "pathogenic")
    summ(bc, "benign    ")
    print("\nbenign detail:")
    for c in sorted(bc, key=lambda c: c["delta"]):
        print(f'  {c["notation"]:22s} {c["site_type"]:9s} delta={c["delta"]:+.3f}  {c["sig"]} [{c["review"][:30]}]')
    print("\nweakest pathogenic:")
    for c in sorted(pc, key=lambda c: c["delta"], reverse=True)[:10]:
        print(f'  {c["notation"]:22s} {c["site_type"]:9s} delta={c["delta"]:+.3f}  [{c["review"][:30]}]')
    Path("tests/fixtures").mkdir(exist_ok=True)
    json.dump({"source": "ClinVar live query 2026-09-21 + RefSeqGene NG_005905.2 windows "
                         "(NM_007294.3 / NP_009225.1 CDS numbering)",
               "pathogenic": pc, "benign": bc},
              open("tests/fixtures/brca1_splice_golden.json", "w"), indent=1)
    print("\nfixture written: tests/fixtures/brca1_splice_golden.json")

if __name__ == "__main__":
    main()
