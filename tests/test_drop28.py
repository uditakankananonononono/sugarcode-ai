"""Drop 28: U12 GT-AG (minor spliceosome) donor routing. U12 GT-AG donors
(RTATCCTTT consensus) are distinguished from U2 GT-AG donors by matrix
score margin 0.15 - calibrated on the vendored sets: >=97% recall on the
361 gold U12 GT-AG donors, <=0.2% FPR on the 1,170 U2 harvest donors.
Acceptor-side U12 discrimination is too weak (41% recall at 6.4% FPR) and
is intentionally NOT routed - documented in STATUS."""
from pathlib import Path

from sugarcode.bio import splice as sp
from sugarcode.bio.pwm import normalized_score
from sugarcode.modules.deepsplice import donor_subtype, variant_at

DATA = Path("src/sugarcode/bio/data/splice_sites")
U12 = [l.split("\t") for l in (DATA / "u12_sites.tsv").read_text().splitlines()[1:]]


def test_donor_subtype_classes():
    assert donor_subtype("ACTGTATCC") == "U12 GT-AG"   # gold U12 window
    assert donor_subtype("AAGGTAAGT") == "U2 GT-AG"
    assert donor_subtype("AAGATAAGT") == "AT-AC"
    assert donor_subtype("AAGGCAAGT") == "GC-AG"
    assert donor_subtype("AAGAAAAGT") == "other"


def test_u12_gtag_calibration_recall_and_fpr():
    """Hermetic calibration regression on the vendored sets."""
    u2d, u12d = sp.donor_lod(), sp.u12_gtag_donor_lod()
    gold = [r[1] for r in U12 if r[0] == "GTAG"]
    assert len(gold) == 361
    recall = sum(1 for w in gold if donor_subtype(w) == "U12 GT-AG") / len(gold)
    assert recall >= 0.97
    rows = [l.split("\t") for l in (DATA / "junctions.tsv").read_text().splitlines()[1:]]
    u2 = [r[3] for r in rows if r[5] == "1" and r[3][3:5] == "GT"]
    fpr = sum(1 for w in u2 if donor_subtype(w) == "U12 GT-AG") / len(u2)
    assert fpr <= 0.002


def test_u12_gtag_variant_routing_and_flag():
    """A +1T>A at a U12 GT-AG donor is scored with the U12 matrix (loss),
    carries the subtype flag and calibrated-margin note; a U2 donor is
    untouched by the routing."""
    r = variant_at("ACTGTATCC", 3, "A", "donor")
    assert r["donor_subtype"] == "U12 GT-AG" and r["delta"] <= -0.15
    assert "99.2% recall" in r["u12_note"]
    r2 = variant_at("AAGGTAAGT", 3, "A", "donor")
    assert "donor_subtype" not in r2 and r2["delta"] <= -0.15


def test_pten_c79_flags_u12_candidate():
    """The one U2-harvest junction our margin flags as U12 GT-AG is PTEN
    c.79 (CCTGTATCC - carries the RTATCCT signature). No ClinVar golden
    variant sits at that donor, so pooled golden numbers are unchanged."""
    rows = [l.split("\t") for l in (DATA / "junctions.tsv").read_text().splitlines()[1:]]
    flagged = [(r[0], r[3]) for r in rows if r[5] == "1" and r[3][3:5] == "GT"
               and donor_subtype(r[3]) == "U12 GT-AG"]
    assert flagged == [("PTEN", "CCTGTATCC")]
