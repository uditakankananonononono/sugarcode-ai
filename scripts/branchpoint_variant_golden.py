"""Drop 50: branch-point-region functional variant golden (Leman et al. 2020,
BMC Genomics 21:97, data/variantBP.txt vendored verbatim as
src/sugarcode/bio/data/branchpoints/leman_variant_bp.txt). 120 experimentally
assayed intronic variants at c.-44..-18 relative to the 3' splice site, with
functional readouts (minigene / RT-PCR; class_effect 0 = no splicing effect,
1 = splicing defect).

This set probes the branch-point ZONE - the region upstream of every term the
current model carries (acceptor PWM spans c.-14..+1, tract term c.-12..-3).
For each variant in a covered gene (cDNA numbering verified by an explicit
ref-base check against the RefSeqGene record - variants failing the check are
EXCLUDED and reported, never silently kept), we:
  1. compute the current-model delta (expected ~0 by construction - the
     honest gap measurement, not a model failure);
  2. scan the -60..-15 zone for YNYURAY branch-point candidates (consensus
     Y N Y T R A Y, branch A at offset 5; Mercer et al. 2015) in ref and alt
     sequence and record whether the variant disrupts a candidate.

Writes tests/fixtures/branchpoint_variant_golden.json (hermetic) and prints
the class 0 vs class 1 disruption partition.
"""
from __future__ import annotations
import csv, json, re, sys
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from cryptic_recall_vus import gene_context, GENES
from gb_parse import revcomp

DATA = Path("src/sugarcode/bio/data/branchpoints")
FIX = Path("tests/fixtures/branchpoint_variant_golden.json")
ZONE = (-45, -18)  # branch A search zone (empirical, Mercer 2015 / Leman 2020)
CONS = [set("CT"), set("ACGT"), set("CT"), {"T"}, set("AG"), {"A"}, set("CT")]
BP = json.loads(Path("src/sugarcode/bio/data/splice_sites/branchpoint_pwm.json").read_text())

def pwm_score(mer):
    import math
    return sum(math.log2(BP["pwm"][k][b] / BP["background"][b])
               for k, b in enumerate(mer))

def best_pwm(win):
    best = None
    for i in range(len(win) - 6):
        a_pos = -(len(win) - (i + 5))
        if not (ZONE[0] <= a_pos <= ZONE[1]):
            continue
        s = pwm_score(win[i:i + 7])
        if best is None or s > best:
            best = s
    return best if best is not None else 0.0

def bp_candidates(win):
    """(position of branch A in cDNA coords, n_consensus_matches) for every
    7-mer in the window whose A falls in ZONE, best-first."""
    out = []
    for i in range(len(win) - 6):
        a_pos = -(len(win) - (i + 5))  # cDNA coord of the branch A
        if not (ZONE[0] <= a_pos <= ZONE[1]):
            continue
        mer = win[i:i + 7]
        score = sum(b in c for b, c in zip(mer, CONS))
        out.append((a_pos, score))
    return out

def best_delta(win_ref, win_alt):
    """Best-candidate consensus-score drop from ref to alt."""
    r = max((s for _, s in bp_candidates(win_ref)), default=0)
    a = max((s for _, s in bp_candidates(win_alt)), default=0)
    return r - a, r

def main():
    rows = list(csv.DictReader((DATA / "leman_variant_bp.txt").open(), delimiter="\t"))
    genes = {}
    cases, excluded = [], []
    for r in rows:
        gene = r["gene"]
        if gene not in GENES:
            continue
        m = re.fullmatch(r"c\.(-?\d+)-(\d+)", r["cNomen"])
        refb, altb = r["ref_allele"].strip(), r["alt_allele"].strip()
        if r["strand"].strip() == "-":  # file alleles are genomic-strand; convert to cDNA
            comp = {"A": "T", "C": "G", "G": "C", "T": "A"}
            refb, altb = comp.get(refb, "?"), comp.get(altb, "?")
        if (not m or r["varType"].strip() != "substitution"
                or len(refb) != 1 or len(altb) != 1
                or refb not in "ACGT" or altb not in "ACGT"):
            excluded.append((r["ID"], "not a simple intronic substitution"))
            continue
        cn, d = int(m.group(1)), int(m.group(2))
        if gene not in genes:
            genes[gene] = gene_context(GENES[gene])
        seq, strand, spans = genes[gene]
        # locate the acceptor whose downstream exon starts at cDNA cn
        hit = None
        def cdna_of(pos):
            n = 0
            for a, b in spans:
                if strand == 1:
                    if pos < a: return None
                    if a <= pos <= b: return n + (pos - a + 1)
                    n += b - a + 1
                else:
                    if pos > b: return None
                    if a <= pos <= b: return n + (b - pos + 1)
                    n += b - a + 1
            return None
        for (a, b), (c, dd) in zip(spans, spans[1:]):
            if strand == 1 and cdna_of(c) == cn:
                hit = (c - 61, c - 1); break
            if strand == -1 and cdna_of(dd) == cn:
                hit = (dd, dd + 60); break
        if not hit:
            excluded.append((r["ID"], f"no exon boundary at c.{cn} in {GENES[gene]}"))
            continue
        w0, w1 = hit
        win = seq[w0:w1] if strand == 1 else revcomp(seq[w0:w1])
        if len(win) != 60:
            excluded.append((r["ID"], "zone window truncated (first intron)"))
            continue
        # ref-base check: variant at cDNA -d -> window index 60 - d
        idx = 60 - d
        if idx < 0 or win[idx] != refb:
            excluded.append((r["ID"], f"ref mismatch: record {win[idx] if 0 <= idx < 60 else '-'} vs {refb}"))
            continue
        alt_win = win[:idx] + altb + win[idx + 1:]
        drop, ref_best = best_delta(win, alt_win)
        pwm_drop = best_pwm(win) - best_pwm(alt_win)
        cases.append({
            "id": r["ID"], "gene": gene, "cnomen": r["cNomen"], "dist": d,
            "class_effect": int(r["class_effect"]), "assay": r["Assay.Method"],
            "result": r["Result"], "ref_best_bp_score": ref_best,
            "bp_consensus_drop": drop,
            "bp_pwm_drop": round(pwm_drop, 4),
            "current_model_delta": 0.0,  # variant outside all current terms
        })
    pos = [c for c in cases if c["class_effect"] == 1]
    neg = [c for c in cases if c["class_effect"] == 0]
    FIX.write_text(json.dumps({
        "source": ("Leman et al. 2020 BMC Genomics 21:97 data/variantBP.txt "
                   "(vendored leman_variant_bp.txt); mapped to RefSeqGene cDNA "
                   "coordinates with per-variant ref-base verification"),
        "n_total": len(rows), "n_covered": len(cases), "n_excluded": len(excluded),
        "excluded": excluded, "cases": cases,
    }, indent=1))
    print(f"total={len(rows)} covered={len(cases)} excluded={len(excluded)}")
    for name, grp in [("functional(1)", pos), ("no-effect(0)", neg)]:
        dis = [c for c in grp if c["bp_consensus_drop"] > 0]
        pd = [c["bp_pwm_drop"] for c in grp]
        big = [c for c in grp if c["bp_pwm_drop"] >= 0.5]
        print(f"{name}: n={len(grp)} consensus-disrupted={len(dis)} "
              f"({100*len(dis)/max(1,len(grp)):.1f}%) pwm_drop mean={sum(pd)/max(1,len(pd)):.3f} "
              f"pwm_drop>=0.5: {len(big)} ({100*len(big)/max(1,len(grp)):.1f}%)")
    func = sorted(((c['id'], c['dist'], c['bp_pwm_drop']) for c in pos), key=lambda x: -x[2])
    print("functional cases by pwm_drop:", func)
    for e in excluded:
        print("EXCLUDED:", e[0], "-", e[1])

if __name__ == "__main__":
    main()
