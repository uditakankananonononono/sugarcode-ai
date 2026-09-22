"""Drop 49: consolidated evidence report (docs/EVIDENCE.md, one repro entry
for every headline number)."""
import subprocess
from pathlib import Path


def test_report_regenerates_and_matches():
    subprocess.run(["python3", "scripts/evidence_report.py"], check=True,
                   capture_output=True)
    doc = Path("docs/EVIDENCE.md").read_text()
    assert "unique pathogenic: 2720" in doc
    assert "canonical U2 (GT/GC donor, AG acceptor): 2414/2414" in doc
    assert "benign specificity: 85/86" in doc
    assert "2196 scored, 179 strong-loss" in doc
    assert "977 scored, 106 strong-loss" in doc
    assert "donor -3..-1 1117 cases, acceptor +1 216 cases" in doc
    assert "0 true cryptic creations in 179" in doc
    assert "NOT supported (honest null)" in doc
