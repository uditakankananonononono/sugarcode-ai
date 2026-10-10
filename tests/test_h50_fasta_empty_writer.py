"""One empty writer behavior pin, not a FASTA-conformance claim."""
from sugarcode.bio.fasta import write_fasta


def test_empty_record_list_writes_one_newline():
    assert write_fasta([]) == '\n'
