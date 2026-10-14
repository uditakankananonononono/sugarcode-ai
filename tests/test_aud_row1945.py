from sugarcode.extra_doc.constitutional_ai import audit_principles

def test_audpin_nested_peaks_1945():
    assert audit_principles([('p','c',1),('p','d',9),('q','c',2)]) == {
        'total': 3, 'peaks': {'p': {'c':1,'d':9}, 'q': {'c':2}},
        'weakest': {'p':'c','q':'c'}, 'exposed': 'p'}

def test_audpin_exposed_tie_first_1945():
    assert audit_principles([('x','a',4),('y','b',4)]) == {
        'total': 2, 'peaks': {'x': {'a':4}, 'y': {'b':4}},
        'weakest': {'x':'a','y':'b'}, 'exposed': 'x'}
