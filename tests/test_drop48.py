"""Drop 48: ESRseq (Ke et al. 2011 lineage) ESE/ESS hexamer model vendored
and tested against the drop-45 exonic donor golden. HONEST NULL: exonic-only
ESRseq deltas (only hexamers FULLY inside the exon count - ESRseq is defined
on exonic hexamers; the naive all-overlapping-hexamers version scores
junction-spanning hexamers and showed a spurious positive mean in EVERY
bucket) do NOT separate pathogenic from benign at exon-terminal positions:
pathogenic mean -0.040 (n=330), VUS +0.077, benign -0.002 (n=22), and BENIGN
variants disrupt ESEs at the highest rate (27.3% vs 13.3% pathogenic). The
ESE-disruption hypothesis for the last-exonic-base gap (drop 45) is NOT
supported; the terminal-base mechanism is the extended donor motif (PWM,
drop 45) plus non-hexamer effects. Reported as a null, not spun.
Vendored: 1,182 ESE + 1,090 ESS hexamers verbatim from the Spliceogen
packaging (VCCRI); RESCUE-ESE's own server and the Ke et al. publisher
supplement both 404 (verified 2026-09-22) - provenance in PROVENANCE.md.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0, "src")
from sugarcode.bio.splice import esrseq, esrseq_score

FIX = json.loads(Path("tests/fixtures/esrseq_enrichment.json").read_text())


def test_vendored_model_shape():
    assert len(esrseq("ese")) == 1182
    assert len(esrseq("ess")) == 1090
    assert esrseq("ese")["AGAAGA"] == 1.034
    assert esrseq("ess")["CTTTTA"] == -1.061
    assert esrseq_score("GAAGAAGAAG") > 3.0
    assert esrseq_score("CTTTTACTTTTA") < -3.0


def test_fixture_shape():
    assert len(FIX["cases"]) == 1104
    s = FIX["summary"]
    assert s["pathogenic"]["n"] == 330 and s["benign"]["n"] == 22
    assert s["vus"]["n"] == 480


def test_exonic_only_null_result():
    s = FIX["summary"]
    assert abs(s["pathogenic"]["mean_esrseq_delta_exonic"]) < 0.1
    assert abs(s["benign"]["mean_esrseq_delta_exonic"]) < 0.1
    # benign disrupts at the HIGHEST rate - anti-separation, kept on record
    assert s["benign"]["frac_disrupting_exonic"] > s["pathogenic"]["frac_disrupting_exonic"]


def test_exonic_hexamer_counts():
    for c in FIX["cases"]:
        assert c["n_exonic_hexamers"] == -c["exonic_offset"]


def test_honest_labeling():
    assert "NOT per-variant upgrades" in FIX["source"]
