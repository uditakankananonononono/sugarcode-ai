"""Drop 50: branch-point groundwork - Leman 2020 functional variant golden +
harvest-learned BP-zone model."""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/branchpoint_variant_golden.json").read_text())
BP = json.loads(Path("src/sugarcode/bio/data/splice_sites/branchpoint_pwm.json").read_text())


def test_vendored_sources_verbatim():
    import hashlib
    h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    assert h("src/sugarcode/bio/data/branchpoints/leman_rnaseq_bp.txt") == \
        "0c0b58ce81470254eba8f918df3d486d89da55a14331430885fbb4cedbcbc51b"
    assert h("src/sugarcode/bio/data/branchpoints/leman_variant_bp.txt") == \
        "d7a6afb6198100c8cc080b4aabfb06383a08e8daecb18cc12a926655e69b40f7"


def test_variant_golden_mapping():
    assert FIX["n_total"] == 120
    assert FIX["n_covered"] == 73
    assert FIX["n_excluded"] == 15
    cases = FIX["cases"]
    assert sum(c["class_effect"] == 1 for c in cases) == 8
    assert sum(c["class_effect"] == 0 for c in cases) == 65
    # every variant sits upstream of all current scoring terms (d >= 18)
    assert all(c["dist"] >= 18 for c in cases)
    assert all(c["current_model_delta"] == 0.0 for c in cases)
    # exclusions are loud and reasoned
    assert any("not a simple intronic substitution" in e[1] for e in FIX["excluded"])
    assert any("ref mismatch" in e[1] for e in FIX["excluded"])


def test_direction_consistent_but_small_n():
    pos = [c for c in FIX["cases"] if c["class_effect"] == 1]
    neg = [c for c in FIX["cases"] if c["class_effect"] == 0]
    mp = sum(c["bp_pwm_drop"] for c in pos) / len(pos)
    mn = sum(c["bp_pwm_drop"] for c in neg) / len(neg)
    assert mp > mn  # direction only; n=8 functional, NO specificity claim


def test_bp_pwm_model():
    assert BP["zone"] == [-45, -18]
    assert BP["n_acceptors"] == 646
    assert BP["n_with_candidate"] == 646
    pwm = BP["pwm"]
    assert len(pwm) == 7
    assert pwm[5]["A"] > 0.7          # branch A
    assert pwm[3]["T"] > 0.8          # -2 U (U2 pairing)
    assert pwm[0]["C"] + pwm[0]["T"] > 0.8
    assert set(BP["background"]) == set("ACGT")
    # position distribution mode inside the empirical branch zone
    pos = {int(k): v for k, v in BP["position_distribution"].items()}
    mode = max(pos, key=pos.get)
    assert -30 <= mode <= -21
