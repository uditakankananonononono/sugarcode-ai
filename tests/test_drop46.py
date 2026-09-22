"""Drop 46: cryptic-site scan recall on the drop-42 VUS sweep. Each of the
179 strong-loss VUS and 1,016 weak-VUS controls (delta > -0.05) was scanned
with cryptic_scan on +/-100 nt flanks from the RefSeqGene records
(transcript orientation; genomic positions derived from the same span math
as the junction maps).

Findings, honest:
1. ZERO true cryptic-site creations in EITHER group (0/179 strong, 0/1016
   control) - consistent with the drop-23 validation that cryptic
   activation is rare and far from natural sites (CFTR 3849+10kb). The
   strong-loss VUS mechanism is natural-site loss, full stop.
2. The unrefined scan's 'new site' events were ALL natural-window
   reclassifications (a shifted/threshold-crossing site inside the natural
   window, e.g. BRCA2 c.7976+2C>T GC->GT at the same position): 18/179
   strong (10.1%) vs 136/1016 control (13.4%). The analysis now partitions
   findings by overlap with the natural window; the partition lives in the
   caller (cryptic_scan is window-agnostic by design).
3. Per-variant VUS calls are NOT upgraded on this basis - the fixture
   source says so.
"""
import json
from pathlib import Path

FIX = json.loads(Path("tests/fixtures/cryptic_recall_vus.json").read_text())


def test_results_shape():
    r = FIX["results"]
    assert r["strong"]["n"] == 179 and r["control"]["n"] == 1016
    assert r["strong"]["skipped"] == 0 and r["control"]["skipped"] == 8


def test_no_true_cryptic_sites():
    assert FIX["results"]["strong"]["new"] == 0
    assert FIX["results"]["control"]["new"] == 0
    assert not any(c["new_cryptic"] for c in FIX["strong_with_cryptic"])


def test_natural_reclass_partitioned():
    r = FIX["results"]
    assert r["strong"]["natural_reclass"] == 18
    assert r["control"]["natural_reclass"] == 136
    # every detailed finding must carry the partition fields
    for c in FIX["strong_with_cryptic"]:
        assert "natural_reclass" in c and "cryptic_findings" in c


def test_honest_labeling():
    assert "NOT upgraded" in FIX["source"]
