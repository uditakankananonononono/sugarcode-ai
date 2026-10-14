"""Row828 Progress Monitoring - Tracks advancement.
Supplied ordered progress readings only. Rows(label,value0..100),1..32.
Return consecutive signed changes and labels where reading dropped versus
previous reading. First reading has no previous comparison.
NOT_CLAIMED: verified progress, advancement quality, monitoring integrations,
trend predictions, actual learning outcomes or external effects.
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


def progress_reading_changes(rows):
    _rows(rows,'readings',32,2)
    for label,value in rows:_label(label);_integer(value,0,100)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('reading labels must be unique')
    changes=[(rows[i][0],rows[i][1]-rows[i-1][1]) for i in range(1,len(rows))]
    return {'changes':changes,'drops':[label for label,delta in changes if delta<0],'progress_verified':False}
