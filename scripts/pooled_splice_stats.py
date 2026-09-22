"""Pooled splice-golden statistics across ALL fixture genes (17 as of drop 26),
split by site class. Reproducibility entry for the README/STATUS numbers:
reads only the hermetic fixtures, no network.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

sys.path.insert(0, "src")
from sugarcode.modules.deepsplice import site_class

FIX = sorted(Path("tests/fixtures").glob("*_splice_golden.json"))


def k_of(case):
    return int(re.search(r"[+-](\d+)", case["notation"]).group(1))


def main():
    tot = {"path": 0, "ben": 0}
    canon_u2 = canon_u2_loss = canon_atac = 0
    atac_cases = []
    ben_tp = ben_n = 0
    per_gene = {}
    for f in FIX:
        gene = f.name.replace("_splice_golden.json", "")
        d = json.loads(f.read_text())
        pc, bc = d["pathogenic"], d["benign"]
        tot["path"] += len(pc); tot["ben"] += len(bc)
        cu = cl = ca = 0
        for c in pc:
            if k_of(c) > 2:
                continue
            cls = site_class(c["window"], c["site_type"])
            if cls in ("GT", "GC", "AG"):
                cu += 1
                cl += c["delta"] <= -0.15
            else:
                ca += 1
                atac_cases.append((gene, c["notation"], cls, c["delta"]))
        canon_u2 += cu; canon_u2_loss += cl; canon_atac += ca
        ben_n += len(bc)
        ben_tp += sum(1 for c in bc if c["delta"] > -0.15)
        per_gene[gene] = {"pathogenic": len(pc), "benign": len(bc),
                          "canon_u2": cu, "canon_u2_loss": cl, "canon_atac": ca}
    print(f"genes: {len(FIX)}  pathogenic: {tot['path']}  benign: {tot['ben']}")
    print(f"canonical U2 (GT/GC donor, AG acceptor): {canon_u2_loss}/{canon_u2} called loss")
    atac_loss = sum(1 for _, _, _, dl in atac_cases if dl <= -0.15)
    print(f"canonical AT-AC (U12 matrices, drop 27): {atac_loss}/{canon_atac} called loss")
    for g, n, cls, dl in atac_cases:
        print(f"   {g} {n} class={cls} delta={dl:+.3f}")
    print(f"benign specificity: {ben_tp}/{ben_n}")
    for g, s in sorted(per_gene.items()):
        print(f"   {g:7s} path={s['pathogenic']:4d} ben={s['benign']:3d} "
              f"canon_u2={s['canon_u2_loss']}/{s['canon_u2']} atac={s['canon_atac']}")

if __name__ == "__main__":
    main()
