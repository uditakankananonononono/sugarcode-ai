"""Row500 Financial Modeling - Projects financials.
Supplied-data helper only. Rows (label, period 0..11, revenue 0..1000000, cost 0..1000000). Sum net per period, then report cumulative net and the first period whose cumulative net is at least 0.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: a valid forecast, real financials or external effects.
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


def analyze_model_breakeven(rows):
    _rows(rows, 'periods', 32, 4)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 11)
        _integer(row[2], 0, 1000000)
        _integer(row[3], 0, 1000000)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('period labels must be unique')
    net={}
    for row in rows:
        net[row[1]]=net.get(row[1],0)+row[2]-row[3]
    ordered=sorted(net.items(),key=lambda item:item[0])
    running=0
    cumulative=[]
    even=None
    for period,value in ordered:
        running+=value
        cumulative.append((period,running))
        if even is None and running>=0:
            even=period
    return {'net':ordered,'cumulative':cumulative,'break_even':even,'forecast_valid':False}
