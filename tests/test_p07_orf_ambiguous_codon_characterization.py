"""P07 characterization (authored, NOT RUN): find_orfs across an ambiguous codon.

Pins the current return value for one literal forward-strand input whose
middle codon is NNN. Expected values are derived by reading
src/sugarcode/bio/orf.py, not observed. Findings only: this records what the
implementation returns for this one input. It makes no claim about biological
accuracy, IUPAC handling in general, the reverse strand, nested or truncated
policies, other genetic-code tables, or alternative starts.
"""
from sugarcode.bio import orf


def test_find_orfs_scan_continues_through_ambiguous_codon_forward_only():
    # Frame +1 codons: ATG, NNN, TAA. NNN is neither a start nor a stop, so the
    # open ATG start survives it and closes at TAA. protein comes from
    # translate("ATGNNN") == "MX" (translation, not scanner, owns X).
    # length_nt 9, length_aa 9 // 3 - 1 == 2. gc counts only the ACGT bases of
    # ATGNNNTAA (A, T, G, T, A, A = 6, of which G is the one GC) -> round(1/6, 6).
    assert orf.find_orfs("ATGNNNTAA", both_strands=False) == [
        {
            "strand": "+",
            "frame": 1,
            "start": 0,
            "end": 9,
            "length_nt": 9,
            "length_aa": 2,
            "gc": 0.166667,
            "start_codon": "ATG",
            "stop_codon": "TAA",
            "truncated": False,
            "protein": "MX",
        }
    ]
