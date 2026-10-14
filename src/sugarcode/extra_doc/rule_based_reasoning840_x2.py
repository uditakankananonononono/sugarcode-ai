"""Row840 Rule-Based Reasoning - Applies rules.
Supplied monotone single-premise implication closure only. Rows(label,premise
integer0..15,conclusion0..15),1..32;facts exact list/tuple0..16 distinct integers
0..15. Return sorted least fixed-point facts. Rules do not negate facts.
NOT_CLAIMED: real-world inference, rule truth, sound knowledge, general
reasoning, action execution or external effects.
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


def implication_closure(rows,facts):
    _rows(rows,'rules',32,3)
    for label,premise,conclusion in rows:_label(label);_integer(premise,0,15);_integer(conclusion,0,15)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('rule labels must be unique')
    if type(facts) not in (list,tuple):raise TypeError('facts: exact list or tuple required')
    if len(facts)>16:raise ValueError('facts: at most16 entries')
    for fact in facts:_integer(fact,0,15)
    if len(set(facts))!=len(facts):raise ValueError('facts must be unique')
    reached=set(facts)
    for _ in range(16):
        next_facts=reached|{conclusion for _,premise,conclusion in rows if premise in reached}
        if next_facts==reached:break
        reached=next_facts
    return {'facts':sorted(reached),'rules_verified':False}
