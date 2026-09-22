"""Drop 53: re-score the two branch-point goldens through the WIRED public
function (deepsplice.branchpoint_variant_effect), lock equivalence with the
analysis-script scores, and attach the weighted wired delta to every case.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from cryptic_recall_vus import gene_context, GENES
from sugarcode.modules.deepsplice import branchpoint_variant_effect, BP_WEIGHT

def window_for(sym, cn):
    seq, strand, spans = gene_context(GENES[sym])
    n = 0
    for a, b in spans:
        if n and n + 1 == cn:
            w = seq[a - 61:a - 1]
            return w if len(w) == 60 else None
        n += b - a + 1
    return None

def main():
    # branchzone fixture: keys notation c.N-dB>A
    fz = Path("tests/fixtures/branchzone_clinvar_golden.json")
    data = json.loads(fz.read_text())
    n_eq = 0
    for sym, g in data["genes"].items():
        for c in g["cases"]:
            m = re.fullmatch(r"c\.(\d+)-(\d+)([ACGT])>([ACGT])", c["notation"])
            cn, d, altb = int(m.group(1)), int(m.group(2)), m.group(4)
            w = window_for(sym, cn)
            r = branchpoint_variant_effect(w, 60 - d, altb)
            assert r["bp_drop_bits"] == c["bp_pwm_drop"], (sym, c["notation"])
            c["wired_delta"] = r["delta"]
            n_eq += 1
    fz.write_text(json.dumps(data, indent=1))
    print(f"branchzone: {n_eq} cases equivalent, wired_delta attached")
    # Leman functional fixture: cnomen c.N-d (alleles in notation id)
    fl = Path("tests/fixtures/branchpoint_variant_golden.json")
    data = json.loads(fl.read_text())
    n_eq = 0
    for c in data["cases"]:
        m = re.fullmatch(r"c\.(\d+)-(\d+)", c["cnomen"])
        cn, d = int(m.group(1)), int(m.group(2))
        altb = c["id"].rsplit(">", 1)[1][-1]
        w = window_for(c["gene"], cn)
        r = branchpoint_variant_effect(w, 60 - d, altb)
        assert r["bp_drop_bits"] == c["bp_pwm_drop"], (c["id"])
        c["wired_delta"] = r["delta"]
        n_eq += 1
    fl.write_text(json.dumps(data, indent=1))
    print(f"leman: {n_eq} cases equivalent, wired_delta attached")

if __name__ == "__main__":
    main()
