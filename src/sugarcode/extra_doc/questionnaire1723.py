"""Doc row1723 Questionnaire Construction: PARTIAL fixed-choice answer audit.

questions exact list1..50 tuples(id,choices,required); choices exact list2..10
unique valid labels, required exact bool. answers exact dict0..50 ID->label.
All labels nonblank exact str<=80, question IDs distinct. Report missing required
IDs, unknown answer IDs and invalid supplied choices. No wording, measurement,
response validity, UI rendering or survey deployment claimed.
"""


def _label(x):return type(x) is str and 1<=len(x)<=80 and bool(x.strip())


def audit(questions,answers):
    if type(questions) is not list or not 1<=len(questions)<=50:
        raise ValueError('questions must be an exact list with 1..50 entries')
    ids=set()
    for row in questions:
        if type(row) is not tuple or len(row)!=3:
            raise ValueError('question must be an id choices required tuple')
        name,choices,required=row
        if not _label(name) or name in ids:raise ValueError('question IDs must be unique valid labels')
        ids.add(name)
        if type(choices) is not list or not 2<=len(choices)<=10 or any(not _label(x) for x in choices) or len(set(choices))!=len(choices):
            raise ValueError('choices must be an exact list of 2..10 unique valid labels')
        if type(required) is not bool:raise ValueError('required must be an exact boolean')
    if type(answers) is not dict or len(answers)>50:
        raise ValueError('answers must be an exact dict with 0..50 entries')
    if any(not _label(x) for pair in answers.items() for x in pair):
        raise ValueError('answer IDs and values must be valid labels')
    return {'missing':[n for n,c,r in questions if r and n not in answers],
            'unknown':[n for n in answers if n not in ids],
            'invalid_choices':[n for n,c,r in questions if n in answers and answers[n] not in c],
            'claim':'PARTIAL','measurement_validated':False}
