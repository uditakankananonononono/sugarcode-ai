"""Drop 44 validation: re-score EVERY golden case with the tract-term model
straight from its fixture window/index/alt (offline, no network) and compare
against the fixture's recorded (pre-tract) delta. Verifies the regression
locks: canonical +/-1/-2 capture unchanged by construction, benign
specificity re-measured (this is the number that could move).
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, "src")
from sugarcode.modules.deepsplice import variant_at, site_class

FIX = sorted(Path("tests/fixtures").glob("*_splice_golden.json"))
FIX = [f for f in FIX if f.name not in ("vus_splice_golden.json",
                                        "conflicting_splice_golden.json",
                                        "cftr_cryptic_golden.json")]

def alt_of(c):
    return re.search(r">([ACGT])$", c["notation"]).group(1)

def main():
    canon = canon_loss = 0
    ben = ben_ok = 0
    moved = []
    for f in FIX:
        d = json.loads(f.read_text())
        for sig in ("pathogenic", "benign"):
            for c in d.get(sig, []):
                if c.get("index") is None or "window" not in c:
                    continue
                res = variant_at(c["window"], c["index"], alt_of(c), c["site_type"])
                k = int(re.search(r"[+-](\d+)", c["notation"]).group(1))
                if sig == "pathogenic" and k <= 2 and \
                        site_class(c["window"], c["site_type"]) in ("GT", "GC", "AG"):
                    canon += 1
                    canon_loss += res["delta"] <= -0.15
                if sig == "benign":
                    ben += 1
                    ben_ok += res["delta"] > -0.15
                if abs(res["delta"] - c["delta"]) > 1e-9:
                    moved.append((f.name, c["notation"], c["delta"], res["delta"]))
    print(f"canonical +/-1/-2 (re-scored): {canon_loss}/{canon} called loss")
    print(f"benign specificity (re-scored): {ben_ok}/{ben}")
    print(f"cases whose delta moved with the tract term: {len(moved)}")
    for name, n, old, new in moved[:5]:
        print(f"   {name} {n}: {old:+.4f} -> {new:+.4f}")

if __name__ == "__main__":
    main()
