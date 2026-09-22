"""GJB2 5'-UTR intron golden (drop 32). GJB2's CDS is a single exon
(intronless coding), but its 5' UTR has one intron - the site of the
well-known splice variants c.-23+1G>A (donor) and c.-22-2A>C / c.-22-1G>A
(acceptor, expert panel). Junction windows come from the NM_004004.6 mRNA
exons on NG_008358.1 (CDS-based harness cannot see UTR introns).

Scope honesty: this golden exercises SCORING (deepsplice variant_at) on the
real UTR windows. live_splice_assessment does NOT yet route negative
(UTR) c. numbers - it answers "outside scope"; that routing extension is
the documented follow-on.
"""
from __future__ import annotations
import json, re, sys

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from sugarcode.modules.deepsplice import variant_at
from gb_parse import parse_genbank, transcript_exons

def utr_junctions():
    txt = entrez._get("efetch.fcgi", {"db": "nuccore", "id": "NG_008358.1",
                                      "rettype": "gb", "retmode": "text"}).decode()
    gb = parse_genbank(txt); seq = gb["sequence"]
    mrna = next(f for f in gb["features"]
                if f["key"] == "mRNA" and f["qualifiers"].get("transcript_id", "").startswith("NM_004004"))
    (a, b), (c, d) = transcript_exons(mrna)
    assert mrna["strand"] == 1
    return seq[b-3:b+6], seq[c-15:c]

def clinvar_utr():
    ids = entrez.esearch("clinvar", 'GJB2[gene] AND "splice"[All Fields]', retmax=200)
    docs = entrez.esummary("clinvar", ids)
    pat = re.compile(r"NM_004004\.\d+\(GJB2\):c\.(-23\+|-22-)(\d+)([ACGT])>([ACGT])")
    rows = []
    for uid, doc in docs.items():
        m = pat.search(doc.get("title", ""))
        if not m: continue
        germ = doc.get("germline_classification", {})
        desc = (germ.get("description", "") or "").lower()
        if "pathogenic" in desc and "conflicting" not in desc:
            cls = "pathogenic"
        elif "benign" in desc and "pathogenic" not in desc and "conflicting" not in desc:
            cls = "benign"
        else:
            continue
        rows.append({"site": m.group(1), "k": int(m.group(2)), "ref": m.group(3),
                     "alt": m.group(4), "sig": cls, "clinvar_sig": germ.get("description", ""),
                     "review": germ.get("review_status", "")})
    return rows

def main():
    donor, acceptor = utr_junctions()
    assert donor == "CAGGTGAGC" and acceptor == "TTCGTCTTTTCCAGA", (donor, acceptor)
    cases = []
    for r in clinvar_utr():
        if r["site"] == "-23+" and r["k"] <= 6:
            w, idx, st = donor, 3 + r["k"] - 1, "donor"
        elif r["site"] == "-22-" and r["k"] <= 14:
            w, idx, st = acceptor, 14 - r["k"], "acceptor"
        else:
            continue
        if w[idx] != r["ref"]:
            continue
        res = variant_at(w, idx, r["alt"], st)
        cases.append({"notation": f"c.{r['site']}{r['k']}{r['ref']}>{r['alt']}",
                      "site_type": st, "window": w, "index": idx, "delta": res["delta"],
                      "sig": r["sig"], "clinvar_sig": r["clinvar_sig"],
                      "review": r["review"], "consequence": res["consequence"]})
    json.dump({"source": "ClinVar live query 2026-09-22 (GJB2 NM_004004, 5'-UTR intron "
                         "splice variants) + NG_008358.1 mRNA-exon windows; CDS is a "
                         "single exon so the CDS harness cannot see this intron",
               "cases": cases},
              open("tests/fixtures/gjb2_utr_golden.json", "w"), indent=1)
    for c in sorted(cases, key=lambda c: c["notation"]):
        print(f'{c["notation"]:16s} {c["sig"]:10s} {c["clinvar_sig"]:28s} delta={c["delta"]:+.3f} [{c["review"][:35]}]')

if __name__ == "__main__":
    main()
