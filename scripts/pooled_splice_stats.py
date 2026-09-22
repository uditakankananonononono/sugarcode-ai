"""Pooled splice-golden statistics across ALL fixture genes (28 genes + SCN-family AT-AC as of drop 35),
split by site class. Reproducibility entry for the README/STATUS numbers:
reads only the hermetic fixtures, no network.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

sys.path.insert(0, "src")
from sugarcode.modules.deepsplice import site_class

FIX = sorted(Path("tests/fixtures").glob("*_splice_golden.json"))
# drop 35: the SCN-family AT-AC golden rides along (SCN1A's 8 AT-AC cases
# are already in the main fixtures; these are the 8 NEW family cases)
FIX += sorted(Path("tests/fixtures").glob("*_u12_golden.json"))
FIX += sorted(Path("tests/fixtures").glob("*_u12_gtag_golden.json"))  # PTEN (drop 31)


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
        if "cases" in d:  # U12 golden format (drop 31/35): sig-tagged cases
            pc = [c for c in d["cases"] if c["sig"] == "pathogenic"]
            bc = [c for c in d["cases"] if c["sig"] == "benign"]
            gene = f.name.split("_u12")[0] + ("_scn" if "scn_atac" in f.name else "")
        else:
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
    # drop 31 overlap: pten_u12_gtag's acceptor trio (c.80-1G>A/C, c.80-2A>C)
    # also sits in the main pten fixture - dedupe the pooled totals by
    # (gene, notation); per-gene rows stay as recorded
    seen = set()
    for f in FIX:
        d = json.loads(f.read_text())
        g = f.name.split("_u12")[0].replace("_splice_golden.json", "").replace("_golden.json", "")
        rows = d.get("pathogenic", []) or [c for c in d["cases"] if c["sig"] == "pathogenic"]
        for c in rows:
            seen.add((g, c["notation"]))
    print(f"genes: {len(FIX)}  pathogenic: {tot['path']}  benign: {tot['ben']}")
    print(f"unique (gene, notation) pathogenic after dedupe: {len(seen)}")
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
