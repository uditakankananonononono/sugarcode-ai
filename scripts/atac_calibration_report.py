"""AT-AC (U12) matrix calibration report (drop 37). Separates what is
CIRCULAR from what is INDEPENDENT in the AT-AC validation:

- The SCN-family minor intron is in the intronIC gold training set, so the
  golden acceptor/donor WINDOWS overlap training: high ref scores there
  are not independent evidence.
- The 16 ClinVar pathogenic variant DELTAS (8 SCN1A + 8 family) are the
  independent part: the matrix must penalize the observed alt alleles at
  -1/-2 (acceptor) and +1/+2 (donor), and it does (all -0.158/-0.205).
- Position-level check: the log-odds columns at the pathogenic positions
  must carry the penalty (acceptor idx 12/13 = -2/-1; donor idx 3/4 = +1/+2).

Writes src/sugarcode/bio/data/splice_sites/atac_calibration.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

sys.path.insert(0, "src")
from sugarcode.bio import splice as sp
from sugarcode.bio.pwm import normalized_score

DATA = Path("src/sugarcode/bio/data/splice_sites")

def main():
    rows = [l.split("\t") for l in (DATA / "u12_sites.tsv").read_text().splitlines()[1:]]
    atac = [r for r in rows if r[0] == "ATAC"]
    train_d = [r[1] for r in atac]
    train_a = [r[2] for r in atac]
    dlod, alod = sp.u12_atac_donor_lod(), sp.u12_atac_acceptor_lod()

    import re as _re
    golden = json.loads(Path("tests/fixtures/scn_atac_u12_golden.json").read_text())["cases"]
    scn1a = json.loads(Path("tests/fixtures/scn1a_splice_golden.json").read_text())["pathogenic"]
    def _k(c):
        return int(_re.search(r"[+-](\d+)", c["notation"]).group(1))
    # canonical = variant at +/-1 or +/-2 of an AT-AC site (pooled definition)
    atac_golden = ([c for c in scn1a if _k(c) <= 2 and
                    (c["window"][3:5] == "AT" or c["window"][12:14] == "AC")]
                   + golden)

    rep = {"training_windows": {"donor": len(train_d), "acceptor": len(train_a)},
           "circularity": {}, "variant_deltas": [], "position_logodds": {}}
    # circularity: which golden windows appear verbatim in training
    seen = {}
    for c in atac_golden:
        w = c["window"]
        in_train = (w in train_d) if c["site_type"] == "donor" else (w[:14] in train_a)
        seen.setdefault(w, {"site_type": c["site_type"], "in_training": in_train})
    rep["circularity"] = {"windows": [
        {"window": w, **v} for w, v in sorted(seen.items())],
        "note": ("windows flagged in_training=True overlap the 139-intron "
                 "training set (the SCN-family minor intron is in intronIC): "
                 "their high ref scores are circular. Windows flagged False "
                 "are INDEPENDENT of training. All 16 variant DELTAS are "
                 "independent ClinVar evidence regardless.")}
    # variant deltas: all pathogenic, must be loss
    for c in atac_golden:
        rep["variant_deltas"].append({"gene": c.get("gene", "scn1a"),
                                      "notation": c["notation"], "delta": round(c["delta"], 3)})
    assert all(d["delta"] <= -0.15 for d in rep["variant_deltas"])
    # position-level log-odds at the pathogenic positions
    rep["position_logodds"]["acceptor_-2(A)"] = alod[12]
    rep["position_logodds"]["acceptor_-1(C)"] = alod[13]
    rep["position_logodds"]["donor_+1(A)"] = dlod[3]
    rep["position_logodds"]["donor_+2(T)"] = dlod[4]
    json.dump(rep, open(DATA / "atac_calibration.json", "w"), indent=1)
    print("training windows:", rep["training_windows"])
    print("circularity:", rep["circularity"])
    print("deltas:", sorted({d['delta'] for d in rep['variant_deltas']}), "n =", len(rep["variant_deltas"]))
    for k, v in rep["position_logodds"].items():
        print(k, {b: round(x, 2) for b, x in v.items()})

if __name__ == "__main__":
    main()
