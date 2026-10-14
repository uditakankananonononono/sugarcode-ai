"""Row810 Exercise - Maintains health.
Supplied completed-session minutes arithmetic only. Rows(label,minutes0..1440,
intensity0..100),1..32;threshold0..100. Return minutes at/above threshold and
below threshold, with total minutes. No prescription or health verification.
NOT_CLAIMED: health maintenance, exercise advice, safe intensity, actual
activity verification, calories or external effects.
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


def session_minutes(rows,threshold):
    _rows(rows,'sessions',32,3);_integer(threshold,0,100)
    for label,minutes,intensity in rows:_label(label);_integer(minutes,0,1440);_integer(intensity,0,100)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('session labels must be unique')
    high=sum(m for _,m,i in rows if i>=threshold)
    low=sum(m for _,m,i in rows if i<threshold)
    return {'at_or_above':high,'below':low,'total':high+low,'health_evaluated':False}
