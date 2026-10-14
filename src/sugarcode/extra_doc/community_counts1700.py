"""Community Engagement.

PARTIAL: caller invited/participated count ledger only, not community
engagement, representativeness, consultation quality, consent or policy advice.
Caller counts are declarations, not verified participants or community views.
"""
from fractions import Fraction
SCOPE='caller invited-participated count ledger only; no community engagement or consent claims'


def participation(rows):
    """Exactlist/tuple1..64 triples(label,invited,participated);printable Unicode
    exactstr labels1..40,repeated labels aggregate;exactint0<=participated<=invited
    <=1000000. Sorted(label,invited sum,participated sum,fraction or None at zero
    invited),totals,overall fraction. Mixedrows accepted;participation is not
    agreement,representation,consent or permission. No actual outreach sent.
    """
    if type(rows) not in (list,tuple) or not 1<=len(rows)<=64:raise ValueError('rows must be exactlist/tuple length1..64')
    groups={}
    for row in rows:
        if type(row) not in (list,tuple) or len(row)!=3:raise ValueError('row must be exactlist/tuple triple')
        label,invited,participated=row
        if type(label) is not str or not 1<=len(label)<=40 or not all(ch.isprintable() for ch in label):raise ValueError('label must be exactstr printable Unicode length1..40')
        if type(invited) is not int or type(participated) is not int or not 0<=participated<=invited<=1000000:raise ValueError('counts must be exactint0<=participated<=invited<=1000000')
        old_invited,old_participated=groups.get(label,(0,0));groups[label]=(old_invited+invited,old_participated+participated)
    result=tuple((label,invited,participated,Fraction(participated,invited) if invited else None) for label,(invited,participated) in sorted(groups.items()))
    invited=sum(row[1] for row in result);participated=sum(row[2] for row in result)
    return {'participation':result,'invited':invited,'participated':participated,'fraction':Fraction(participated,invited) if invited else None,'scope':SCOPE}
