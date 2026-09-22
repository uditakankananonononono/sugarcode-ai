"""Harvest real human splice-junction windows from NCBI RefSeqGene records.

Fetches RefSeqGene (NG_) GenBank records for a panel of clinically relevant
genes, parses mRNA join features, and extracts donor (9 nt) and acceptor
(15 nt) windows for every intron. Canonical-filtered windows are vendored
under src/sugarcode/bio/data/splice_sites/.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from sugarcode.bio.pwm import build_pwm
from gb_parse import parse_genbank, revcomp, transcript_exons

GENES = ["BRCA1","BRCA2","TP53","MLH1","MSH2","MSH6","PMS2","CFTR","PAH","PTEN",
         "APC","ATM","RB1","NF1","LDLR","HBB","SCN1A","MECP2","CHEK2","PALB2",
         "MUTYH","KCNQ1","GJB2","F8","DMD","MYH7","PKD1","TSC1","TSC2","VHL"]

OUT = Path("src/sugarcode/bio/data/splice_sites")

def refseqgene_accession(sym: str) -> str | None:
    """Pick the RefSeqGene record for THIS gene - the gene-name query also
    returns neighboring loci (BRCA2's query returns ZAR1L NG_017006.2 first),
    so the record title must contain the symbol."""
    ids = entrez.esearch("nuccore", f"{sym}[gene] AND refseqgene[filter]", retmax=8)
    fallback = None
    for uid, doc in entrez.esummary("nuccore", ids).items():
        acc = doc.get("accessionversion", "")
        if not acc.startswith("NG_"):
            continue
        title = doc.get("title", "")
        if f"({sym})" in title or f" {sym} " in title or title.startswith(f"Homo sapiens {sym} "):
            return acc
        fallback = fallback or acc
    return fallback

def junction_windows(seq: str, mrna: dict) -> list[tuple[str, str]]:
    """(donor9, acceptor15) per intron, transcript orientation."""
    exons = transcript_exons(mrna)
    out = []
    for (a, b), (c, d) in zip(exons, exons[1:]):
        if mrna["strand"] == 1:
            donor = seq[b - 3 : b + 6]            # 1-based b-2..b+6
            acceptor = seq[c - 15 : c]            # 1-based c-14..c
        else:
            donor = revcomp(seq[a - 7 : a + 2])   # 1-based a-6..a+2, rc
            acceptor = revcomp(seq[b - 1 : b + 14])  # 1-based b..b+14, rc
        if len(donor) == 9 and len(acceptor) == 15 and "N" not in donor + acceptor:
            out.append((donor, acceptor))
    return out

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, meta, missing = [], [], []
    for sym in GENES:
        acc = refseqgene_accession(sym)
        if not acc:
            missing.append(sym); print(f"{sym}: NO RefSeqGene record"); continue
        txt = entrez._get("efetch.fcgi", {"db": "nuccore", "id": acc,
                                          "rettype": "gb", "retmode": "text"}).decode()
        gb = parse_genbank(txt)
        mrnas = [f for f in gb["features"] if f["key"] == "mRNA" and len(f["spans"]) >= 2]
        nj = 0
        for ti, m in enumerate(mrnas):
            for donor, acceptor in junction_windows(gb["sequence"], m):
                rows.append({"gene": sym, "accession": acc, "transcript": ti,
                             "donor": donor, "acceptor": acceptor})
                nj += 1
        meta.append((sym, acc, len(mrnas), nj))
        print(f"{sym}: {acc} transcripts={len(mrnas)} junctions={nj}")
    # canonical stats
    dc = Counter(d["donor"][3:5] for d in rows)
    ac = Counter(d["acceptor"][12:14] for d in rows)
    print("donor +1+2:", dict(dc.most_common(6)))
    print("acceptor -2-1:", dict(ac.most_common(6)))
    gt_ag = [d for d in rows if d["donor"][3:5] == "GT" and d["acceptor"][12:14] == "AG"]
    donors = sorted({d["donor"] for d in gt_ag})
    acceptors = sorted({d["acceptor"] for d in gt_ag})
    print(f"total junctions={len(rows)} GT-AG={len(gt_ag)} unique donors={len(donors)} unique acceptors={len(acceptors)}")
    # write TSV (all junctions, canonical flag)
    with open(OUT / "junctions.tsv", "w") as fh:
        fh.write("gene\taccession\ttranscript_idx\tdonor9\tacceptor15\tcanonical\n")
        for d in rows:
            canon = d["donor"][3:5] == "GT" and d["acceptor"][12:14] == "AG"
            fh.write(f"{d['gene']}\t{d['accession']}\t{d['transcript']}\t{d['donor']}\t{d['acceptor']}\t{int(canon)}\n")
    # PWMs from unique canonical windows
    dp = build_pwm(donors); ap = build_pwm(acceptors)
    json.dump({"window": 9, "n_sites": len(donors), "pwm": dp}, open(OUT / "donor_pwm.json", "w"))
    json.dump({"window": 15, "n_sites": len(acceptors), "pwm": ap}, open(OUT / "acceptor_pwm.json", "w"))
    # consensus check
    def cons(pwm):
        return "".join(max(col, key=col.get) for col in pwm)
    print("donor consensus:", cons(dp), " acceptor consensus:", cons(ap))
    json.dump({"genes": [{"gene": s, "accession": a, "transcripts": t, "junctions": j}
                         for s, a, t, j in meta], "missing": missing},
              open(OUT / "harvest_meta.json", "w"), indent=2)

if __name__ == "__main__":
    main()

