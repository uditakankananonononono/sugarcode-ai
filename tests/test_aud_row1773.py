from sugarcode.extra_doc.democratization1773 import compare_scores

def test_audpin_reorder_1773():
    assert compare_scores(['a','b'],[(5,[3,7]),(1,[0,10]),(9,[10,0])]) == {
        'changes': [('a',0,10,10),('b',10,0,-10)],
        'means': [(1,(5,1)),(5,(5,1)),(9,(5,1))],
        'claim': 'PARTIAL', 'democracy_inferred': False}

def test_audpin_two_waves_1773():
    assert compare_scores(['x'],[(0,[0]),(2,[1])]) == {
        'changes': [('x',0,1,1)],
        'means': [(0,(0,1)),(2,(1,1))],
        'claim': 'PARTIAL', 'democracy_inferred': False}

def test_audpin_reduction_1773():
    assert compare_scores(['p','q','r'],[(4,[1,2,3]),(0,[6,6,6])]) == {
        'changes': [('p',6,1,-5),('q',6,2,-4),('r',6,3,-3)],
        'means': [(0,(6,1)),(4,(2,1))],
        'claim': 'PARTIAL', 'democracy_inferred': False}
