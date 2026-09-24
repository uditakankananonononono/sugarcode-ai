"""bio.kmer k-mer toolkit (drop 77)."""
import math

import pytest

from sugarcode.bio import kmer as km


def test_fnv1a64_reference_vectors():
    # Published FNV-1a 64-bit reference values (isthe.com/chongo/tech/comp/fnv)
    assert km.fnv1a64("") == 0xCBF29CE484222325
    assert km.fnv1a64("a") == 0xAF63DC4C8601EC8C
    assert km.fnv1a64("foobar") == 0x85944171F73967E8


def test_canonical_kmer_strand_collapse():
    assert km.canonical_kmer("AAA") == "AAA"
    assert km.canonical_kmer("TTT") == "AAA"
    assert km.canonical_kmer("ACG") == "ACG"
    assert km.canonical_kmer("CGT") == "ACG"
    assert km.canonical_kmer("AT") == "AT"  # even-k palindrome, no special case


def test_iter_kmers_skips_ambiguous_windows():
    assert list(km.iter_kmers("AACGNTT", 2, canonical=False)) == \
        ["AA", "AC", "CG", "TT"]
    assert list(km.iter_kmers("nAc", 2)) == ["AC"]


def test_count_kmers_hand_computed_and_strand_collapsed():
    assert km.count_kmers("AAAA", 2) == {"AA": 3}
    assert km.count_kmers("AACGNTT", 2) == {"AA": 2, "AC": 1, "CG": 1}
    # reverse complements count identically under canonical collapse
    assert km.count_kmers("AACG", 2) == km.count_kmers("CGTT", 2)


def test_kmer_edge_cases():
    with pytest.raises(ValueError):
        list(km.iter_kmers("ACGT", 0))
    assert km.count_kmers("AC", 5) == {}
    assert km.count_kmers("", 2) == {}
    assert km.kmer_set("NNNN", 2) == set()


def test_set_operations():
    r = km.set_operations({"A", "C"}, {"A", "B"})
    assert r["union"] == {"A", "B", "C"}
    assert r["intersection"] == {"A"}
    assert r["difference"] == {"C"}
    assert r["symmetric_difference"] == {"B", "C"}


def test_jaccard_and_containment_math():
    assert km.jaccard({"A", "C"}, {"A", "B"}) == pytest.approx(1 / 3)
    assert km.jaccard({"A"}, {"A"}) == 1.0
    assert km.jaccard(set(), set()) == 1.0       # documented convention
    assert km.jaccard(set(), {"A"}) == 0.0
    assert km.containment({"A", "C"}, {"A", "C", "D"}) == 1.0
    assert km.containment({"A", "C"}, {"A", "B"}) == pytest.approx(0.5)
    assert km.containment(set(), {"A"}) == 0.0


def test_compare_sequences_hand_computed():
    r = km.compare_sequences("AAAA", "AAAT", 2)
    assert r["size_a"] == 1 and r["size_b"] == 2 and r["shared"] == 1
    assert r["jaccard"] == pytest.approx(0.5)
    assert r["containment_a_in_b"] == 1.0
    assert r["containment_b_in_a"] == pytest.approx(0.5)


def test_minimizers_lex_hand_computed():
    # kmers TG,GC,CA,AT,TG,GC,CA; windows of 3 -> CA,AT,AT,AT,CA -> {AT,CA}
    assert km.minimizers("TGCATGCA", 2, 3, canonical=False,
                         order="lex") == ["AT", "CA"]
    # tie inside one window: rightmost kept, set still the single k-mer
    assert km.minimizers("ACAC", 2, 3, canonical=False,
                         order="lex") == ["AC"]


def test_minimizers_short_stream_and_errors():
    # stream shorter than w -> single global minimum (Roberts 2004)
    assert km.minimizers("ACG", 2, 5, order="lex") == ["AC"]
    assert km.minimizers("NN", 2, 5) == []
    with pytest.raises(ValueError):
        km.minimizers("ACGT", 2, 0)
    with pytest.raises(ValueError):
        km.minimizers("ACGT", 2, 2, order="md5")


def test_minimizers_w1_is_exact_and_deterministic():
    seq = "ACGTACGTACGTTTGGCCAANNACGT"
    assert set(km.minimizers(seq, 3, 1, order="hash")) == km.kmer_set(seq, 3)
    assert km.minimizers(seq, 4, 3) == km.minimizers(seq, 4, 3)
    r = km.compare_sketches("AAAA", "AAAT", 2, 1)
    assert r["jaccard_estimate"] == pytest.approx(0.5)  # w=1 -> exact


def test_mash_distance_math():
    assert km.mash_distance(1.0, 21) == 0.0
    assert km.mash_distance(0.0, 21) == math.inf
    assert km.mash_distance(0.5, 2) == pytest.approx(math.log(1.5) / 2)
    with pytest.raises(ValueError):
        km.mash_distance(0.5, 0)


def test_compare_files_pools_records(tmp_path):
    fa = tmp_path / "a.fa"; fa.write_text(">r1\nAAAA\n>r2\nCC\n")
    fb = tmp_path / "b.fa"; fb.write_text(">r1\nAAAA\n")
    r = km.compare_files(fa, fb, 2)
    assert r["size_a"] == 2 and r["size_b"] == 1 and r["shared"] == 1
    assert r["jaccard"] == pytest.approx(0.5)
    assert r["containment_b_in_a"] == 1.0
    fq = tmp_path / "c.fastq"; fq.write_text("@r1\nAAAA\n+\nIIII\n")
    r2 = km.compare_files(fa, fq, 2)
    assert r2["size_b"] == 1
    bad = tmp_path / "x.txt"; bad.write_text("not a sequence file\n")
    with pytest.raises(ValueError):
        km.load_sequences(bad)  # first char is neither '>' nor '@'
