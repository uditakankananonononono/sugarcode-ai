"""Multi-gene golden validation: deepsplice PWM vs ClinVar splice variants
for BRCA2, MLH1, CFTR (extends the BRCA1 harness). Writes per-gene fixtures.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from sugarcode.modules.deepsplice import variant_at
from gb_parse import parse_genbank, transcript_exons

GENES = {"BRCA2": "NG_012772.3", "MLH1": "NG_007109.2", "CFTR": "NG_016465.4",
         "MSH2": "NG_007110.2", "TP53": "NG_017013.2", "NF1": "NG_009018.1"}

# ClinVar names variants on specific transcript versions; the record's
# span-matching can pick an isoform name on ties (TP53: NM_001126114.2 ties
# canonical NM_000546.5). Override with the transcript ClinVar uses; the
# junction MAP is unaffected (it comes from the canonical CDS spans).
TX_OVERRIDE = {"TP53": "NM_000546"}


def load_gene(acc: str):
    """Canonical-transcript junctions + cDNA map from a RefSeqGene record.

    Canonical = the CDS with the most spans (full-length transcript).
    Internal CDS span boundaries ARE the splice junctions (UTR trimming only
    differs at the terminal exons), so junctions come straight from the CDS:
    no mRNA-matching step to get wrong."""
    txt = entrez._get("efetch.fcgi", {"db": "nuccore", "id": acc,
                                      "rettype": "gb", "retmode": "text"}).decode()
    gb = parse_genbank(txt); seq = gb["sequence"]
    cds = max((f for f in gb["features"] if f["key"] == "CDS" and len(f["spans"]) >= 2),
              key=lambda c: len(c["spans"]))
    strand = cds["strand"]
    cds_spans = transcript_exons(cds)
    def cdna_of(pos):
        n = 0
        for a, b in cds_spans:
            if strand == 1:
                if pos < a: return None
                if a <= pos <= b: return n + (pos - a + 1)
                n += b - a + 1
            else:
                if pos > b: return None
                if a <= pos <= b: return n + (b - pos + 1)
                n += b - a + 1
        return None
    from gb_parse import revcomp
    donors, acceptors = {}, {}
    for (a, b), (c, d) in zip(cds_spans, cds_spans[1:]):
        if strand == 1:
            donors[cdna_of(b)] = seq[b-3:b+6]
            acceptors[cdna_of(c)] = seq[c-15:c]
        else:
            donors[cdna_of(a)] = revcomp(seq[a-7:a+2])
            acceptors[cdna_of(d)] = revcomp(seq[d-1:d+14])
    donors = {k: v for k, v in donors.items() if k is not None}
    acceptors = {k: v for k, v in acceptors.items() if k is not None}
    # tx name = mRNA sharing the most spans with this CDS (the first mRNA
    # with >= spans is NOT reliable: TP53's record lists NM_001126118.1
    # before canonical NM_000546.5)
    cds_set = set(cds["spans"])
    tx = ""
    best = -1
    for f in gb["features"]:
        if f["key"] != "mRNA":
            continue
        shared = len(cds_set & set(f["spans"]))
        if shared > best:
            best = shared
            tx = f["qualifiers"].get("transcript_id", "")
    return donors, acceptors, tx, seq


def clinvar_splice(sym: str, nm_prefix: str, sig_filter: str):
    ids = entrez.esearch("clinvar",
                         f'{sym}[gene] AND "splice"[All Fields] AND "clinsig {sig_filter}"[Properties]',
                         retmax=1000)
    docs = {}
    for i in range(0, len(ids), 100):
        docs.update(entrez.esummary("clinvar", ids[i:i+100]))
    pat = re.compile(rf'{nm_prefix}\.\d+\({sym}\):c\.(\d+)([+-])(\d+)([ACGT])>([ACGT])')
    rows = []
    for uid, doc in docs.items():
        m = pat.search(doc.get("title", ""))
        if not m: continue
        germ = doc.get("germline_classification", {})
        rows.append({"uid": uid, "sig": germ.get("description", ""),
                     "review": germ.get("review_status", ""),
                     "n": int(m.group(1)), "sign": m.group(2), "k": int(m.group(3)),
                     "ref": m.group(4), "alt": m.group(5)})
    return rows


def build_cases(rows, donors, acceptors, cls):
    cases = []
    for r in rows:
        if r["sign"] == "+" and r["k"] <= 6:
            w = donors.get(r["n"]); idx = 3 + r["k"] - 1; st = "donor"
        elif r["sign"] == "-" and r["k"] <= 14:
            w = acceptors.get(r["n"]); idx = 14 - r["k"]; st = "acceptor"
        else:
            continue
        if not w or w[idx] != r["ref"]:
            continue
        res = variant_at(w, idx, r["alt"], st)
        cases.append({"notation": f"c.{r['n']}{r['sign']}{r['k']}{r['ref']}>{r['alt']}",
                      "site_type": st, "window": w, "index": idx,
                      "ref_score": res["ref_score"], "alt_score": res["alt_score"],
                      "delta": res["delta"], "sig": cls, "review": r["review"],
                      "consequence": res["consequence"]})
    return cases


def main():
    summary = {}
    for sym, acc in GENES.items():
        donors, acceptors, tx, seq = load_gene(acc)
        nm = TX_OVERRIDE.get(sym, tx.rsplit(".", 1)[0])
        pc = build_cases(clinvar_splice(sym, nm, "pathogenic"), donors, acceptors, "pathogenic")
        bc = build_cases(clinvar_splice(sym, nm, "benign"), donors, acceptors, "benign")
        json.dump({"source": f"ClinVar live query 2026-09-22 + RefSeqGene {acc} windows "
                             f"({tx} CDS numbering)", "pathogenic": pc, "benign": bc},
                  open(f"tests/fixtures/{sym.lower()}_splice_golden.json", "w"), indent=1)
        canon = [c for c in pc if int(re.search(r"[+-](\d+)", c["notation"]).group(1)) <= 2]
        canon_loss = sum(1 for c in canon if c["delta"] <= -0.15)
        tp = sum(1 for c in pc if c["delta"] <= -0.15)
        tn = sum(1 for c in bc if c["delta"] > -0.15)
        summary[sym] = {"tx": tx, "pathogenic": len(pc), "benign": len(bc),
                        "canonical": len(canon), "canonical_loss": canon_loss,
                        "sens": round(tp/len(pc), 3) if pc else None,
                        "spec": round(tn/len(bc), 3) if bc else None}
        print(sym, summary[sym])
        # show benign outliers honestly
        for c in sorted(bc, key=lambda c: c["delta"])[:3]:
            print(f'   weakest benign: {c["notation"]} delta={c["delta"]:+.3f} [{c["review"][:35]}]')
        for c in sorted(pc, key=lambda c: -c["delta"])[:0]:
            pass
    json.dump(summary, open("/tmp/multigene_summary.json", "w"), indent=1)

if __name__ == "__main__":
    main()
