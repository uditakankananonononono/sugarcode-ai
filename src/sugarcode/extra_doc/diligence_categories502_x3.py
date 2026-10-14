"""Row502 Due Diligence Preparation - Organizes for review.
Supplied-data helper only. Rows (label, category 0..5, status 0 missing/1 partial/2 done, weight 1..10). Return done and total weight per present category and sorted categories holding a missing item.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a ready data room, legal readiness or external effects.
"""
def _rows(value, name, cap, arity):
    if type(value) not in (list, tuple): raise TypeError(name + ': exact list or tuple required')
    if not 1 <= len(value) <= cap: raise ValueError(name + ': row count outside declared range')
    for row in value:
        if type(row) not in (list, tuple): raise TypeError(name + ': exact list or tuple row required')
        if len(row) != arity: raise ValueError(name + ': wrong row arity')


def _label(value):
    if type(value) is not str: raise TypeError('exact string label required')
    if not 1 <= len(value) <= 24 or not value.isascii() or not all(c.isalnum() or c == '_' for c in value):
        raise ValueError('label must be 1..24 ASCII word characters')


def _integer(value, lo, hi):
    if type(value) is not int: raise TypeError('exact nonbool integer required')
    if not lo <= value <= hi: raise ValueError('integer outside declared range')


def analyze_diligence_categories(rows):
    _rows(rows, 'documents', 32, 4)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 5)
        _integer(row[2], 0, 2)
        _integer(row[3], 1, 10)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('document labels must be unique')
    done={}
    total={}
    for row in rows:
        total[row[1]]=total.get(row[1],0)+row[3]
        done[row[1]]=done.get(row[1],0)+(row[3] if row[2]==2 else 0)
    return {'categories':[(category,done[category],total[category]) for category in sorted(total)],'blocked':sorted({row[1] for row in rows if row[2]==0}),'review_ready':False}
