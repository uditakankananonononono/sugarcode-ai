"""Row825 Metacognition - Thinks about thinking.
Supplied prediction confidence calibration arithmetic only. Rows(label,
confidence_bps0..10000,observed_bit0..1),1..32. Return exact mean squared
probability error (Brier score), per-label signed probability error.
NOT_CLAIMED: actual metacognition, thinking quality, valid observations,
calibrated future beliefs, mental assessment or external effects.
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


def declared_prediction_errors(rows):
    _rows(rows,'predictions',32,3)
    for label,confidence,observed in rows:_label(label);_integer(confidence,0,10000);_integer(observed,0,1)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('prediction labels must be unique')
    from fractions import Fraction
    errors=[(label,Fraction(confidence,10000)-observed) for label,confidence,observed in sorted(rows)]
    return {'errors':errors,'brier':sum(error*error for _,error in errors)/len(errors),'metacognition_evaluated':False}
