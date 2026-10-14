"""Row 1961, AI Verification.

ai_verification_evidence classifies supplied proof x and counterexample
y evidence counts. Any nonzero counterexample count gives refuted;
otherwise at least required proof counts gives supported; otherwise
unresolved. Returns label-sorted statuses pairs and separate supported,
refuted and unresolved label lists. Labels denote this count rule only:
no proof is checked and no counterexample is validated. No AI verification,
formal proof validation, counterexample validity or model correctness claim.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 10; bool and all subclasses are refused.
required defaults to 2, an exact int from 1 to 5.
Validation order: rows type, rows size, required, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: AI verification, formal proof validation, counterexample validity, model correctness, production readiness.
"""

SCOPE = 'PARTIAL: supplied proof/counterexample count evidence classification, no AI verification'
NOT_CLAIMED = ('AI verification', 'formal proof validation', 'counterexample validity', 'model correctness', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def ai_verification_evidence(rows, required=2):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(required) is not int or not 1 <= required <= 5:
        raise ValueError('required must be a nonbool integer between 1 and 5')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 10:
            raise ValueError('x must be a nonbool integer between 0 and 10')
        if type(y) is not int or not 0 <= y <= 10:
            raise ValueError('y must be a nonbool integer between 0 and 10')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    statuses=sorted((n,'refuted' if y>0 else ('supported' if x>=required else 'unresolved')) for n,x,y in clean)
    return {'statuses':statuses,'supported':[n for n,s in statuses if s=='supported'],
            'refuted':[n for n,s in statuses if s=='refuted'],'unresolved':[n for n,s in statuses if s=='unresolved']}
