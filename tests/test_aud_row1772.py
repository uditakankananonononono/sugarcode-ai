from sugarcode.extra_doc.revolution1772 import audit_changes

def test_audpin_unsorted_1772():
    assert audit_changes([(5,'a'),(0,'a'),(9,'b'),(3,'a'),(20,'b')]) == {
        'changes': [(5,'a',9,'b')],
        'runs': [('a',0,5,3),('b',9,20,2)],
        'claim': 'PARTIAL', 'revolution_inferred': False}

def test_audpin_alternating_1772():
    assert audit_changes([(0,'x'),(1,'y'),(2,'x')]) == {
        'changes': [(0,'x',1,'y'),(1,'y',2,'x')],
        'runs': [('x',0,0,1),('y',1,1,1),('x',2,2,1)],
        'claim': 'PARTIAL', 'revolution_inferred': False}

def test_audpin_single_run_1772():
    assert audit_changes([(0,'a'),(1,'a')]) == {
        'changes': [], 'runs': [('a',0,1,2)],
        'claim': 'PARTIAL', 'revolution_inferred': False}

def test_audpin_gap_runs_1772():
    assert audit_changes([(7,'m'),(8,'m'),(9,'n'),(400,'n'),(401,'m')]) == {
        'changes': [(8,'m',9,'n'),(400,'n',401,'m')],
        'runs': [('m',7,8,2),('n',9,400,2),('m',401,401,1)],
        'claim': 'PARTIAL', 'revolution_inferred': False}
