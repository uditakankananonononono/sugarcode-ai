"""Row815 Elaborative Interrogation - Asks why.
Supplied why-question reason-annotation checklist only. Rows(label,reason_count
0..100,minimum_reasons0..100),1..32. Report per-label positive shortfall,
satisfied labels, exact supplied reason total. Counts do not establish meaning.
NOT_CLAIMED: meaningful reasons, asking why, understanding, learning
improvement, valid explanations or external effects.
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


def reason_annotation_gaps(rows):
    _rows(rows,'questions',32,3)
    for label,count,minimum in rows:_label(label);_integer(count,0,100);_integer(minimum,0,100)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('question labels must be unique')
    return {'gaps':[(label,minimum-count) for label,count,minimum in sorted(rows) if count<minimum],
            'satisfied':[label for label,count,minimum in sorted(rows) if count>=minimum],
            'reason_total':sum(count for _,count,_ in rows),'understanding_evaluated':False}
