from sugarcode.extra_doc.fair_ai import count_breakaways

def test_audpin_leapfrog_1951():
    assert count_breakaways([('m','a',5),('m','b',6),('m','a',7)]) == {
        'total': 3, 'breakaways': {'b':1,'a':1}, 'count': 2, 'leader': 'a'}

def test_audpin_tie_no_breakaway_1951():
    assert count_breakaways([('m','a',5),('m','b',5)]) == {
        'total': 2, 'breakaways': {}, 'count': 0, 'leader': None}
