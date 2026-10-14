"""Doc row1722 Survey Design: PARTIAL supplied question/construct coverage.

Constructs exact list1..20 unique nonblank exact str<=80. Questions exact list
0..50 tuples(id,construct,required), distinct IDs valid labels, construct valid
label (may be unknown), required exact bool. Return uncovered constructs,
unknown question IDs and optional-only constructs in construct input order.
No valid survey measurement, wording, sampling or respondent recruitment claim.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit(constructs,questions):
    if type(constructs) is not list or not 1<=len(constructs)<=20:
        raise ValueError('constructs must be an exact list with 1..20 entries')
    if any(not _label(x) for x in constructs) or len(set(constructs))!=len(constructs):
        raise ValueError('constructs must be unique valid labels')
    if type(questions) is not list or len(questions)>50:
        raise ValueError('questions must be an exact list with 0..50 entries')
    ids=set()
    for row in questions:
        if type(row) is not tuple or len(row)!=3:
            raise ValueError('question must be an id construct required tuple')
        name,construct,required=row
        if not _label(name) or name in ids:raise ValueError('question IDs must be unique valid labels')
        ids.add(name)
        if not _label(construct):raise ValueError('question construct must be a valid label')
        if type(required) is not bool:raise ValueError('required must be an exact boolean')
    coverage={c:[] for c in constructs};unknown=[]
    for name,c,required in questions:
        if c in coverage:coverage[c].append(required)
        else:unknown.append(name)
    return {'uncovered':[c for c in constructs if not coverage[c]],'unknown':unknown,
            'optional_only':[c for c in constructs if coverage[c] and not any(coverage[c])],
            'claim':'PARTIAL','survey_validated':False}
