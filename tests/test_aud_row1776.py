from sugarcode.extra_doc.ethnicity1776 import count_labels

def test_audpin_mixed_1776():
    assert count_labels([('a',['p','q']),('b',[]),('c',['q'])]) == {
        'frequencies': [('p',1),('q',2)], 'unlabelled': ['b'], 'multiple': ['a'],
        'claim': 'PARTIAL', 'ethnicity_inferred': False}

def test_audpin_single_1776():
    assert count_labels([('solo',['m'])]) == {
        'frequencies': [('m',1)], 'unlabelled': [], 'multiple': [],
        'claim': 'PARTIAL', 'ethnicity_inferred': False}
