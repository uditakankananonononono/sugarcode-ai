"""Ocean Fertilization.

PARTIAL: caller abstract resource/requirement limiting-ratio arithmetic only,
not ocean fertilization,biological productivity,carbon uptake or intervention
safety. Resources/requirements caller declarations,not validated ocean chemistry.
"""
from fractions import Fraction
SCOPE='caller abstract limiting-resource ratios only; no ocean productivity or uptake claims'


def limits(rows):
    """Exactlist/tuple1..64 rows(label,available,per_unit),unique printable Unicode
    exactstr1..40 labels;available exactint0..1000000,per_unit exactint1..1000000.
    Return sorted(label,exact available/per_unit),minimum supported units and
    all tied labels. No rounding,resource interactions,organisms or chemistry
    inferred. Mixedrows accepted;minimum only abstract caller requirement model.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    labels=set();result=[]
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,available,per_unit=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if label in labels:raise ValueError('labels must be unique')
        labels.add(label)
        if type(available) is not int or not 0<=available<=1000000:raise ValueError('available must be exactint0..1000000')
        if type(per_unit) is not int or not 1<=per_unit<=1000000:raise ValueError('per_unit must be exactint1..1000000')
        result.append((label,Fraction(available,per_unit)))
    result.sort(key=lambda row:row[0]);minimum=min(row[1] for row in result)
    return {'limits':tuple(result),'supported_units':minimum,'limiting':tuple(label for label,value in result if value==minimum),'scope':SCOPE}
