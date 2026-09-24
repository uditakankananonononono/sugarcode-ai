import csv, io, sys
from pathlib import Path
import pytest
torch = pytest.importorskip("torch")
from sugarcode.tools import splice_vus_triage as t

FIX = Path(__file__).with_name("data_splice_triage_fixture.tsv")

def test_reproduces_committed_scores():
    # expected values are the scores committed in mega27-01 discovery/splice_region_vus/vus_cnn_scores.tsv.gz
    for r in csv.DictReader(open(FIX), delimiter="\t"):
        assert abs(t.cnn_score(r["ref_ctx"], r["alt_ctx"], t.parse_offset(r["name"])) - float(r["expected_cnn"])) < 1e-4

def test_offset_parsing_and_limits():
    assert t.parse_offset("NM_1.1(X):c.100+5G>A") == 5
    assert t.parse_offset("NM_1.1(X):c.100-12T>C") == -12
    with pytest.raises(ValueError):
        t.parse_offset("NM_1.1(X):c.100+19A>T")

def test_calibration_ppv_monotone():
    a = t.calibrated(0.99, 0.03)["ppv"]; b = t.calibrated(0.85, 0.03)["ppv"]
    assert a > b > 0 and t.calibrated(0.1, 0.03)["ppv"] is None

def test_cli_context_mode(capsys):
    assert t.main([str(FIX)]) == 0
    out = list(csv.DictReader(io.StringIO(capsys.readouterr().out), delimiter="\t"))
    assert len(out) == 3 and all(o["tier"] for o in out) and not any(o["error"] for o in out)
