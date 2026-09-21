"""Extended multi-gene golden validation: 10 more mapped genes beyond the
original 7 (validate_multigene_splice.py). Same harness; writes per-gene
fixtures. Reproduces tests/fixtures/{apc,atm,ldlr,mecp2,msh6,pah,pms2,pten,
rb1,scn1a}_splice_golden.json exactly (live ClinVar + NCBI, 2026-09-22).

Transcript handling discovered during the run (all verified live):
- APC:  record span-match picks NM_001127511.1; ClinVar cites NM_000038.
- SCN1A: ClinVar cites NM_001165963, which carries a 33-nt alternative
  coding exon ABSENT from NG_011906.1's annotation (only NM_006920.4
  annotated). Insertion sits between NM_006920 cDNA 2556|2557: every
  downstream ClinVar junction is cited +33. We remap n>2589 by -33; each
  surviving case is ref-base verified (42 -> 97 mapped, zero mismatches).
  Variants inside the alt exon itself (2557..2589) cannot map: dropped.
- MECP2: ClinVar cites NM_001110792, not the record's NM_004992.4.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from validate_multigene_splice import load_gene, clinvar_splice, build_cases

GENES = {"MSH6": "NG_007111.1", "PMS2": "NG_008466.1", "APC": "NG_008481.4",
         "ATM": "NG_009830.1", "RB1": "NG_009009.1", "PTEN": "NG_007466.2",
         "PAH": "NG_008690.2", "LDLR": "NG_009060.1", "SCN1A": "NG_011906.1",
         "MECP2": "NG_007107.3"}

TX_OVERRIDE = {"APC": "NM_000038", "SCN1A": "NM_001165963", "MECP2": "NM_001110792"}

# SCN1A only: NM_001165963 -> NM_006920 cDNA coordinate remap (see docstring)
COORD_SHIFT = {"SCN1A": (2589, -33)}   # (shift if n > after, delta)


def main():
    summary = {}
    for sym, acc in GENES.items():
        donors, acceptors, tx, seq = load_gene(acc)
        nm = TX_OVERRIDE.get(sym, tx.rsplit(".", 1)[0])
        def cases(sig):
            rows = clinvar_splice(sym, nm, sig)
            if sym in COORD_SHIFT:
                after, delta = COORD_SHIFT[sym]
                rows = [dict(r, n=r["n"] + delta) if r["n"] > after else r
                        for r in rows]
            return build_cases(rows, donors, acceptors, sig)
        pc, bc = cases("pathogenic"), cases("benign")
        note = (f"; ClinVar transcript {nm} via TX_OVERRIDE" if sym in TX_OVERRIDE else "")
        if sym in COORD_SHIFT:
            note += (f"; {nm} citations remapped {COORD_SHIFT[sym][1]} for "
                     f"cDNA>{COORD_SHIFT[sym][0]} (33-nt alt exon absent from record; "
                     "per-variant ref-base verified)")
        json.dump({"source": f"ClinVar live query 2026-09-22 + RefSeqGene {acc} windows "
                             f"({tx} CDS numbering{note})",
                   "pathogenic": pc, "benign": bc},
                  open(f"tests/fixtures/{sym.lower()}_splice_golden.json", "w"), indent=1)
        canon = [c for c in pc if int(re.search(r"[+-](\d+)", c["notation"]).group(1)) <= 2]
        canon_loss = sum(1 for c in canon if c["delta"] <= -0.15)
        tp = sum(1 for c in pc if c["delta"] <= -0.15)
        tn = sum(1 for c in bc if c["delta"] > -0.15)
        summary[sym] = {"tx": tx, "nm_used": nm, "pathogenic": len(pc), "benign": len(bc),
                        "canonical": len(canon), "canonical_loss": canon_loss,
                        "sens": round(tp/len(pc), 3) if pc else None,
                        "spec": round(tn/len(bc), 3) if bc else None}
        print(sym, summary[sym], flush=True)
    json.dump(summary, open("/tmp/extended_summary.json", "w"), indent=1)

if __name__ == "__main__":
    main()
