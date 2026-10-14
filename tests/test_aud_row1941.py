from sugarcode.extra_doc.agent_coordination import tighten_spans

def test_audpin_widening_not_tightening_1941():
    assert tighten_spans([('a','c',9),('b','c',1),('a','c',9)]) == {
        'total': 3, 'sums': {'a':18,'b':1}, 'tightenings': 0, 'span': 17}

def test_audpin_single_agent_1941():
    assert tighten_spans([('solo','c',5)]) == {
        'total': 1, 'sums': {'solo':5}, 'tightenings': 0, 'span': 0}
