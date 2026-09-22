"""Drop 55: U12 acceptor +1 exonic column - uniform placeholder replaced
with the U2 learned column (documented approximation, zero fixture impact)."""
import json
from pathlib import Path

D = Path("src/sugarcode/bio/data/splice_sites")


def test_u12_acceptor_col14_real():
    u2 = json.loads((D / "acceptor_pwm.json").read_text())["pwm"][14]
    for f in ("u12_atac_acceptor_pwm.json", "u12_gtag_acceptor_pwm.json"):
        col = json.loads((D / f).read_text())["pwm"][14]
        assert col != {"A": 0.25, "C": 0.25, "G": 0.25, "T": 0.25}
        for b in "ACGT":
            assert abs(col[b] - u2[b]) < 1e-9
        assert col["G"] > 0.45  # acceptor-exon +1 G preference


def test_no_u12_fixture_case_at_acceptor_plus1():
    import re
    for f in ("tests/fixtures/pten_u12_gtag_golden.json",
              "tests/fixtures/scn_atac_u12_golden.json"):
        s = Path(f).read_text()
        assert not re.search(r'c\.\d+[ACGT]>[ACGT]', s)  # no exonic coding subs
