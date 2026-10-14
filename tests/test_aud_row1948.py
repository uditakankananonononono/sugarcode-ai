from sugarcode.extra_doc.ai_ethics import count_revisits

def test_audpin_triple_revisit_1948():
    assert count_revisits([('d','f',1),('d','f',2),('d','f',3)]) == {
        'total': 3, 'revisits': {'f':2}, 'revisited': ['d'], 'leader': 'f'}

def test_audpin_distinct_pairs_1948():
    assert count_revisits([('a','x',1),('b','x',1),('a','y',1)]) == {
        'total': 3, 'revisits': {}, 'revisited': [], 'leader': None}
