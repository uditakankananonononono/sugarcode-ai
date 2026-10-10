"""Source-derived orphan GS findings. Authored, NOT RUN."""
from sugarcode.bio.stockholm import parse_stockholm, write_stockholm


def test_literal_orphan_gs_is_stored_without_sequence():
    parsed = parse_stockholm('# STOCKHOLM 1.0\ns AC\n#=GS zz DE orphan\n//\n')
    assert parsed['gs'] == {'DE': {'zz': 'orphan'}}
    assert parsed['seqs'] == [('s', 'AC')]
    assert 'zz' not in [name for name, _ in parsed['seqs']]


def test_literal_orphan_gs_survives_parse_write_parse():
    parsed = parse_stockholm('# STOCKHOLM 1.0\ns AC\n#=GS zz DE orphan\n//\n')
    reparsed = parse_stockholm(write_stockholm(parsed))
    assert reparsed == parsed
    assert reparsed['gs'] == {'DE': {'zz': 'orphan'}}
    assert reparsed['seqs'] == [('s', 'AC')]
    assert 'zz' not in [name for name, _ in reparsed['seqs']]
