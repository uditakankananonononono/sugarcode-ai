from sugarcode.extra_doc.trustworthy_ai import count_silvers

def test_audpin_shared_silver_1953():
    assert count_silvers([('a','t',9),('b','t',5),('c','t',5)]) == {
        'total': 3, 'silvers': {'b':1,'c':1}, 'count': 2, 'outright': 1, 'leader': 'b'}

def test_audpin_tied_top_no_silver_no_outright_1953():
    assert count_silvers([('a','t',9),('b','t',9)]) == {
        'total': 2, 'silvers': {}, 'count': 0, 'outright': 0, 'leader': None}
