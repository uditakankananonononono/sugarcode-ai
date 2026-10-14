"""Row817 Dual Coding - Combines verbal and visual.
Supplied verbal/visual attachment-count checklist only. Rows(label,verbal_count
0..100,visual_count0..100),1..32. Return paired min(counts), unmatched counts,
and labels missing either modality. Counts do not establish semantic linkage.
NOT_CLAIMED: actual dual coding, linked meanings, learning improvement,
visual interpretation, attachment creation or external effects.
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


def modality_pair_counts(rows):
    _rows(rows,'concepts',32,3)
    for label,verbal,visual in rows:_label(label);_integer(verbal,0,100);_integer(visual,0,100)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('concept labels must be unique')
    reports=[(label,min(v,w),max(v-w,0),max(w-v,0)) for label,v,w in sorted(rows)]
    return {'pairs':reports,'missing_modality':[label for label,v,w in sorted(rows) if v==0 or w==0],'learning_evaluated':False}
