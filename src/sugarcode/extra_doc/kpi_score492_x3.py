"""Row492 KPI Selection - Chooses metrics.
Supplied-data helper only. Rows (label, relevance 0..10, measurability 0..10). Select metrics with relevance at least 7 and measurability at least 5, ranked by their product descending then label.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: valid metrics, performance or external effects.
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


def analyze_kpi_score(rows):
    _rows(rows, 'metrics', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 10)
        _integer(row[2], 0, 10)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('metric labels must be unique')
    chosen=sorted(((row[0],row[1]*row[2]) for row in rows if row[1]>=7 and row[2]>=5),key=lambda item:(-item[1],item[0]))
    return {'selected':chosen,'metrics_valid':False}
