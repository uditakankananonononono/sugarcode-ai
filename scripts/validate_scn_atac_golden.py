"""SCN-family AT-AC (U12) golden (drop 35). The SCN1A AT-AC intron is
conserved across the voltage-gated sodium channel family: the same minor
intron exists in SCN2A/4A/5A/8A/9A (intronIC gold set, matched by donor
window on each gene's RefSeqGene record). ClinVar cites DIFFERENT
transcripts than the records' canonical CDS for these genes (SCN2A
NM_001040142, SCN8A NM_001330260, SCN9A NM_001365536), so junction maps
are built with the drop-27 cdna_junction_map (cited-transcript CDS aligned
to the genomic record, coverage ~1.0). SCN2A/5A/8A/9A RefSeqGene records
are map-only extensions to harvest_meta.json - NOT in the PWM training
set, so no matrix or existing golden moves.
"""
from __future__ import annotations
import json, re, sys

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from sugarcode.bio.splice import cdna_junction_map
from sugarcode.modules.deepsplice import variant_at

GENES = {"SCN2A": ("NM_001040142.2", "NG_008143.1", 386),
         "SCN8A": ("NM_001330260.2", "NG_021180.3", 395),
         "SCN9A": ("NM_001365536.1", "NG_012798.1", 377),
         "SCN5A": ("NM_000335.4", "NG_008934.1", 392)}

def clinvar_at(g, nm_prefix, dn):
    ids = entrez.esearch("clinvar", f'{g}[gene] AND "splice"[All Fields]', retmax=1000)
    docs = entrez.esummary("clinvar", ids)
    pat = re.compile(rf"{nm_prefix}\.\d+\({g}\):c\.({dn}\+(\d+)|{dn+1}-(\d+))([ACGT])>([ACGT])")
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
        rows.append({"site": "+" if m.group(2) else "-",
                     "k": int(m.group(2) or m.group(3)), "ref": m.group(4), "alt": m.group(5),
                     "sig": cls, "clinvar_sig": germ.get("description", ""),
                     "review": germ.get("review_status", "")})
    return rows

def main():
    cases = []
    for g, (tx, acc, dn) in GENES.items():
        jm = cdna_junction_map(g, tx)
        assert jm["status"] == "ok", (g, jm["status"])
        for r in clinvar_at(g, tx.rsplit(".", 1)[0], dn):
            if r["site"] == "+" and r["k"] <= 6:
                w, idx, st = jm["donors"][dn], 3 + r["k"] - 1, "donor"
            elif r["site"] == "-" and r["k"] <= 14:
                w, idx, st = jm["acceptors"][dn + 1], 14 - r["k"], "acceptor"
            else:
                continue
            if w[idx] != r["ref"]:
                continue
            res = variant_at(w, idx, r["alt"], st)
            cases.append({"gene": g,
                          "notation": f"c.{dn}{r['site']}{r['k']}{r['ref']}>{r['alt']}"
                                      if r["site"] == "+" else
                                      f"c.{dn+1}-{r['k']}{r['ref']}>{r['alt']}",
                          "site_type": st, "window": w, "index": idx,
                          "delta": res["delta"], "u12_atac": res.get("u12_atac", False),
                          "sig": r["sig"], "clinvar_sig": r["clinvar_sig"],
                          "review": r["review"], "consequence": res["consequence"]})
    json.dump({"source": "ClinVar live query 2026-09-22 on the ClinVar-cited transcripts "
                         "(SCN2A NM_001040142.2, SCN8A NM_001330260.2, SCN9A NM_001365536.1, "
                         "SCN5A NM_000335.4) via cdna_junction_map; AT-AC intron confirmed "
                         "per gene by the intronIC gold set (donor-window match)",
               "cases": cases},
              open("tests/fixtures/scn_atac_u12_golden.json", "w"), indent=1)
    for c in sorted(cases, key=lambda c: (c["gene"], c["notation"])):
        print(f'{c["gene"]:6s} {c["notation"]:16s} {c["clinvar_sig"]:24s} '
              f'delta={c["delta"]:+.3f} u12={c["u12_atac"]} [{c["review"][:30]}]')

if __name__ == "__main__":
    main()
