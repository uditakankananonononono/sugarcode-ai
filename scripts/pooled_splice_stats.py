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
# drop 44: the sweep fixtures (drops 42/43) are classification-bucket sweeps,
# not per-gene goldens - exclude from the pooled golden headline
FIX = [f for f in FIX if f.name not in ("vus_splice_golden.json",
                                        "conflicting_splice_golden.json")]
# drop 35: the SCN-family AT-AC golden rides along (SCN1A's 8 AT-AC cases
# are already in the main fixtures; these are the 8 NEW family cases)
FIX += sorted(Path("tests/fixtures").glob("*_u12_golden.json"))
FIX += sorted(Path("tests/fixtures").glob("*_u12_gtag_golden.json"))  # PTEN (drop 31)
# drop 41: GC-AG donor golden (cases-format; VUS cases carried but counted
# in NEITHER pathogenic nor benign - specificity side has zero benign data)
FIX += sorted(Path("tests/fixtures").glob("gc_donor_golden.json"))


def k_of(case):
    return int(re.search(r"[+-](\d+)", case["notation"]).group(1))


def main():
    # Collect every case into (gene, notation)-keyed maps FIRST, so overlaps
    # between fixtures (drop-31 PTEN trio, drop-41 GC-donor cases also sitting
    # in the main BRCA2/ATM/PALB2 goldens) count ONCE in the pooled headline.
    # Genes are lowercased - the gc fixture carries real gene names while the
    # main fixtures key by filename.
    path_cases, ben_cases = {}, {}
    per_gene = {}
    for f in FIX:
        gene = f.name.replace("_splice_golden.json", "")
        d = json.loads(f.read_text())
        if "cases" in d:  # sig-tagged cases format (U12 goldens, GC golden)
            pc = [c for c in d["cases"] if c["sig"] == "pathogenic"]
            bc = [c for c in d["cases"] if c["sig"] == "benign"]
            if "_u12" in f.name:
                gene = f.name.split("_u12")[0] + ("_scn" if "scn_atac" in f.name else "")
            elif f.name == "gc_donor_golden.json":
                gene = "gc_donor"
                # per-case real genes for the pooled maps
                for c in pc:
                    path_cases[(c["gene"].lower(), c["notation"])] = c
                per_gene[gene] = {"pathogenic": len(pc), "benign": 0}
                continue
        else:
            pc, bc = d["pathogenic"], d["benign"]
        for c in pc:
            path_cases[(gene.lower(), c["notation"])] = c
        for c in bc:
            ben_cases[(gene.lower(), c["notation"])] = c
        per_gene[gene] = {"pathogenic": len(pc), "benign": len(bc)}
    tot_path, tot_ben = len(path_cases), len(ben_cases)
    canon_u2 = canon_u2_loss = canon_atac = 0
    atac_cases = []
    for (g, n), c in path_cases.items():
        if k_of(c) > 2:
            continue
        cls = site_class(c["window"], c["site_type"])
        if cls in ("GT", "GC", "AG"):
            canon_u2 += 1
            canon_u2_loss += c["delta"] <= -0.15
        else:
            canon_atac += 1
            atac_cases.append((g, n, cls, c["delta"]))
    ben_n = len(ben_cases)
    ben_tp = sum(1 for c in ben_cases.values() if c["delta"] > -0.15)
    print(f"fixtures: {len(FIX)}  unique pathogenic: {tot_path}  unique benign: {tot_ben}")
    print("(pooled counts are deduped by (gene, notation) as of drop 41 -")
    print(" the drop-31 PTEN trio and drop-41 GC-donor overlap with the main")
    print(" fixtures counts once)")
    print(f"canonical U2 (GT/GC donor, AG acceptor): {canon_u2_loss}/{canon_u2} called loss")
    atac_loss = sum(1 for _, _, _, dl in atac_cases if dl <= -0.15)
    print(f"canonical AT-AC (U12 matrices, drop 27): {atac_loss}/{canon_atac} called loss")
    for g, n, cls, dl in atac_cases:
        print(f"   {g} {n} class={cls} delta={dl:+.3f}")
    print(f"benign specificity: {ben_tp}/{ben_n}")
    for g, s in sorted(per_gene.items()):
        print(f"   {g:9s} path={s['pathogenic']:4d} ben={s['benign']:3d}")

if __name__ == "__main__":
    main()
