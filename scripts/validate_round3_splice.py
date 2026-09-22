"""Round-3 multi-gene golden validation: 12 more harvested genes beyond the
17 already fixtured (validate_multigene_splice.py + validate_extended_splice.py).
Same harness; writes per-gene fixtures under tests/fixtures/.

RefSeqGene accessions come from the harvest map (junctions.tsv), which
resolved each record live with the title-contains-symbol check (BRCA2/ZAR1L
lesson). Transcript overrides (TX_OVERRIDE) are only set after the
--diagnose pass shows which NM_ ClinVar actually cites for the gene.
"""
from __future__ import annotations
import json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from sugarcode.bio import entrez
from validate_multigene_splice import load_gene, clinvar_splice, build_cases

GENES = {"CHEK2": "NG_008150.2", "PALB2": "NG_007406.1", "MUTYH": "NG_008189.1",
         "F8": "NG_011403.2", "DMD": "NG_012232.1", "MYH7": "NG_007884.1",
         "PKD1": "NG_008617.1", "TSC1": "NG_012386.1", "TSC2": "NG_005895.1",
         "HBB": "NG_059281.1", "GJB2": "NG_008358.1", "VHL": "NG_008212.3"}

# Every entry justified live 2026-09-22: the --diagnose pass shows ClinVar
# cites this NM_ for the gene, and a paired-CDS probe verified the cited
# transcript's CDS spans EXACTLY equal the record's canonical CDS spans
# (so ClinVar c. numbering is native on the canonical junction map).
TX_OVERRIDE = {"CHEK2": "NM_007194", "PALB2": "NM_024675", "F8": "NM_000132",
               "DMD": "NM_004006", "MYH7": "NM_000257", "PKD1": "NM_001009944",
               "TSC1": "NM_000368", "TSC2": "NM_000548", "HBB": "NM_000518",
               "VHL": "NM_000551"}

# MUTYH: ClinVar cites NM_001048174 (transcript variant beta3), which is NOT
# annotated on RefSeqGene NG_008189.1 - use the drop-27 cdna_junction_map
# machinery (NM_001048174.2 CDS aligned to the genomic record, fails loudly).
CDNA_TX = {"MUTYH": "NM_001048174.2"}

# GJB2 is deliberately EXCLUDED: its CDS is a single exon (intronless coding
# sequence), so there are no CDS splice junctions to golden against. Its
# reported splice variants are 5'-UTR intron variants (c.-23+1G>A, c.-22-2A>C)
# outside this harness's CDS-boundary scope - documented in STATUS.


def diagnose():
    """Which NM_ transcripts does ClinVar cite for splice variants per gene?"""
    for sym in GENES:
        ids = entrez.esearch("clinvar",
                             f'{sym}[gene] AND "splice"[All Fields] AND '
                             f'"clinsig pathogenic"[Properties]', retmax=500)
        docs = entrez.esummary("clinvar", ids)
        c = Counter()
        for doc in docs.values():
            for m in re.finditer(r"(NM_\d+)\.\d+\(", doc.get("title", "")):
                c[m.group(1)] += 1
        print(sym, dict(c.most_common(4)))


def main():
    summary = {}
    for sym, acc in GENES.items():
        if sym == "GJB2":
            print("GJB2 skipped: single-exon CDS (intronless coding); "
                  "splice variants are 5'-UTR, outside CDS-junction scope")
            continue
        if sym in CDNA_TX:
            from sugarcode.bio.splice import cdna_junction_map
            jm = cdna_junction_map(sym, CDNA_TX[sym])
            assert jm["status"] == "ok", jm["status"]
            donors, acceptors, tx = jm["donors"], jm["acceptors"], CDNA_TX[sym]
        else:
            donors, acceptors, tx, seq = load_gene(acc)
        nm = TX_OVERRIDE.get(sym, tx.rsplit(".", 1)[0])
        pc = build_cases(clinvar_splice(sym, nm, "pathogenic"), donors, acceptors, "pathogenic")
        bc = build_cases(clinvar_splice(sym, nm, "benign"), donors, acceptors, "benign")
        note = f"; ClinVar transcript {nm} via TX_OVERRIDE" if sym in TX_OVERRIDE else ""
        json.dump({"source": f"ClinVar live query 2026-09-22 + RefSeqGene {acc} windows "
                             f"({tx} CDS numbering{note})",
                   "pathogenic": pc, "benign": bc},
                  open(f"tests/fixtures/{sym.lower()}_splice_golden.json", "w"), indent=1)
        canon = [c for c in pc if int(re.search(r"[+-](\d+)", c["notation"]).group(1)) <= 2]
        canon_loss = sum(1 for c in canon if c["delta"] <= -0.15)
        tp = sum(1 for c in pc if c["delta"] <= -0.15)
        tn = sum(1 for c in bc if c["delta"] > -0.15)
        summary[sym] = {"tx": tx, "nm": nm, "pathogenic": len(pc), "benign": len(bc),
                        "canonical": len(canon), "canonical_loss": canon_loss,
                        "sens": round(tp/len(pc), 3) if pc else None,
                        "spec": round(tn/len(bc), 3) if bc else None}
        print(sym, summary[sym])
        for c in sorted(bc, key=lambda c: c["delta"])[:3]:
            print(f'   weakest benign: {c["notation"]} delta={c["delta"]:+.3f} [{c["review"][:35]}]')
        for c in sorted(pc, key=lambda c: -c["delta"])[:2]:
            print(f'   weakest path:   {c["notation"]} delta={c["delta"]:+.3f} [{c["review"][:35]}]')
    json.dump(summary, open("/tmp/round3_summary.json", "w"), indent=1)


if __name__ == "__main__":
    diagnose() if "--diagnose" in sys.argv else main()
