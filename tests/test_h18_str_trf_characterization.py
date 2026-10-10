"""AUTHORED, NOT RUN. H18: str_scope.find_strs exact-repeat characterization against the frozen TRF 4.09.1 comparison (peer-supplied; archive SHA
7b60ab42b56b7d1fe453d6127ceaaa0c771c84991541a4bf7041d528fedd1ea0). Base f1931559be238a132612ae764575892458b8b223. Test and contract only: product code is untouched and no output is edited or rescored.
Frozen files are vendored byte-identical and hash-pinned; no TRF, no network. In the frozen results JSON "reference" is the TRF side and "actual" is the str_scope side (per the peer's ruling: HBB TRF 0 / module 6).
TIER 1 (8 analytical cases incl. all-N): module spans must equal the frozen TRF spans exactly.
TIER 2 (HBB): every module span is verified exact by brute force string checks; TRF reports none of them, so each is a TRF-OMISSION (coverage, not a false positive);
 the converse (TRF span the module misses) must be empty. The frozen strict-exactness FAIL (HBB exact False, verdict FAIL) is retained. No expansion or pathogenicity accuracy is claimed."""
import hashlib
import json
from pathlib import Path

from sugarcode.modules.str_scope.core import find_strs

FIX = Path(__file__).with_name("fixtures")
FASTA, FREEZE, RESULTS = FIX / "h18_str_trf_input.fasta", FIX / "h18_str_trf_freeze_v2.md", FIX / "h18_str_trf_results.json"
SHA = {FASTA: "40ffa4192ece95dae49199365a477ba81537ba004ebea83c1d0c95dee4f80286",
       FREEZE: "9e4fc95cf86c569e2395c13f7c9dec08b92466025ba5d76e2c2bee567b94b285",
       RESULTS: "1bbe1037155d262af605c4ac0d30d1fb68e2dda7440216996b73cf1ead5d3197"}
ANALYTICAL = ["homopolymer", "CAG", "partial", "ATTC", "compound", "GAA", "reverse", "unknown"]
# the six HBB spans, verbatim from the frozen results (0-based half-open, unit length 1)
HBB_SPANS = [(96, 100, 1, "G"), (188, 192, 1, "G"), (420, 424, 1, "C"), (560, 565, 1, "G"), (604, 610, 1, "A"), (616, 620, 1, "T")]


def _fasta():
    seqs, key = {}, None
    for line in FASTA.read_text().split("\n"):
        if line.startswith(">"):
            key = line[1:]
            seqs[key] = ""
        elif line:
            seqs[key] += line
    return seqs


def _cases():
    return {c["case"]: c for c in json.loads(RESULTS.read_text())["cases"]}


def _proj(spans):
    return sorted((h["span_start"], h["span_end"], h["unit_len"], h["canonical_unit"]) for h in spans)


def _canon(u):
    return min(u[i:] + u[:i] for i in range(len(u)))


def test_vendored_frozen_files_are_hash_pinned():
    for path, sha in SHA.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha, path.name


def test_nine_cases_eight_analytical_incl_all_n_and_one_hbb():
    cases = _cases()
    assert list(cases) == ["HBB"] + ANALYTICAL and set(_fasta()) == set(cases)
    assert [c["exact"] for n, c in cases.items() if n != "HBB"] == [True] * 8 and cases["HBB"]["exact"] is False


def test_frozen_strict_exactness_fail_is_retained():
    r = json.loads(RESULTS.read_text())
    assert r["verdict"] == "FAIL" and r["biological_validation"].startswith("NOT ESTABLISHED")
    hbb = _cases()["HBB"]
    assert hbb["reference"] == [] and len(hbb["actual"]) == 6 and _proj(hbb["actual"]) == sorted(HBB_SPANS)


def test_tier1_analytical_module_spans_equal_frozen_trf_spans():
    seqs, cases = _fasta(), _cases()
    for name in ANALYTICAL:
        assert _proj(find_strs(seqs[name], 1, 6, 4)) == _proj(cases[name]["reference"]), name
    assert find_strs(seqs["unknown"], 1, 6, 4) == []


def test_tier2_hbb_every_module_span_is_exact_by_brute_force():
    s = _fasta()["HBB"]
    hits = find_strs(s, 1, 6, 4)
    assert _proj(hits) == sorted(HBB_SPANS)
    for a, b, u, canon in _proj(hits):
        sl = s[a:b]
        assert 1 <= u <= 6 and len(sl) // u >= 4, (a, b)
        assert all(sl[j] == sl[j + u] for j in range(len(sl) - u)), (a, b)  # 100% matches, no indels
        assert _canon(sl[:u]) == canon, (a, b)
        assert a == 0 or s[a - 1] != s[a - 1 + u], (a, b)  # maximal on the left
        assert b >= len(s) or s[b] != s[b - u], (a, b)  # maximal on the right


def test_tier2_hbb_classification_trf_omission_not_false_positive_and_no_converse():
    cases, s = _cases(), _fasta()["HBB"]
    module = set(_proj(find_strs(s, 1, 6, 4)))
    trf = set(_proj(cases["HBB"]["reference"]))
    omissions = sorted(module - trf)   # valid exact module spans TRF did not report: TRF-OMISSION (coverage), not a false positive
    disagreements = sorted(trf - module)   # TRF spans the module misses: DISAGREEMENT
    assert omissions == sorted(HBB_SPANS) and disagreements == []
