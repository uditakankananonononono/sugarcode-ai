"""Row816 Self-Explanation - Explains to self.
Supplied arithmetic explanation-step ledger only. Rows(label,left integer
-1000..1000,right same,operation0add/1subtract/2multiply,claimed-1000000..1000000),
1..32. Report correct/incorrect exact calculation claims and corrected values.
NOT_CLAIMED: actual self-explanation, reasoning quality, understanding,
pedagogy, semantic correctness outside arithmetic or external effects.
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


def arithmetic_step_checks(rows):
    _rows(rows,'steps',32,5)
    for label,left,right,op,claim in rows:_label(label);_integer(left,-1000,1000);_integer(right,-1000,1000);_integer(op,0,2);_integer(claim,-1000000,1000000)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('step labels must be unique')
    correct=[];corrections=[]
    for label,left,right,op,claim in sorted(rows):
        value=left+right if op==0 else left-right if op==1 else left*right
        if value==claim:correct.append(label)
        else:corrections.append((label,value))
    return {'correct':correct,'corrections':corrections,'understanding_evaluated':False}
