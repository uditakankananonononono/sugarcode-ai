"""Geoengineering.

PARTIAL: caller finite perturbation sensitivity arithmetic only, not
geoengineering,intervention modeling,climate effects,feasibility or safety.
Perturbations/responses supplied by caller,not validated physical experiments.
"""
from fractions import Fraction
SCOPE='caller perturbation sensitivity arithmetic only; no geoengineering effects or safety'


def slopes(rows):
    """Exactlist/tuple1..64 rows(label,delta_input,delta_output),unique printable
    Unicode exactstr1..40 labels;deltas exactint-1000000..1000000,delta_input
    nonzero. Return sorted(label,exact delta_output/delta_input),min/max slope.
    No derivatives,nonlinear extrapolation,causality,units or physical validation.
    Mixedrows accepted;ratios describe only caller pairs,no recommendations.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,dx,dy=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(dx) is not int or type(dy) is not int or not -1000000<=dx<=1000000 or not -1000000<=dy<=1000000:raise ValueError('deltas must be exactint-1000000..1000000')
        if dx==0:raise ValueError('input delta must be nonzero')
        result.append((label,Fraction(dy,dx)))
    return {'slopes':tuple(sorted(result,key=lambda row:row[0])),'minimum':min(row[1] for row in result),
            'maximum':max(row[1] for row in result),'scope':SCOPE}
