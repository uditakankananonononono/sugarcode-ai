"""Row 494, Performance Management (PARTIAL: one exact review check): each review is
an exact tuple (employee, rating, improvements) - employee an exact string of 1 to 24
lowercase identifier characters, rating an exact integer 0 to 5, improvements an exact
integer 0 to 10 of agreed improvement actions. A review is checked against two
evaluation bars, and each bar it fails adds (index, code) to problems:
  rating below 2, else (i, 'failing');
  improvements below 1, else (i, 'stagnant').
Checks run in this order: reviews must be an exact list; review count must be at most
40; each review must be an exact tuple; each review must have 3 items; employee must
be an exact string; employee must be 1 to 24 lowercase identifier characters; rating
must be an exact integer; rating must be 0 to 5; improvements must be an exact
integer; improvements must be 0 to 10. Returns {'problems': sorted, 'employees':
sorted distinct, 'total': number of reviews}.

NOT_CLAIMED: this checks supplied review numbers against two evaluation bars. It does
not say performance improves, that 2 stars or 1 action are the right bars, or that any
rating is fair. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_reviews(reviews):
    """Flag reviews outside the evaluation bars."""
    if type(reviews) is not list:
        raise TypeError('reviews must be an exact list')
    if len(reviews) > 40:
        fail('review count must be at most 40')
    problems = []
    names = set()
    for i, review in enumerate(reviews):
        if type(review) is not tuple:
            raise TypeError('each review must be an exact tuple')
        if len(review) != 3:
            fail('each review must have 3 items')
        employee, rating, improvements = review
        if type(employee) is not str:
            raise TypeError('employee must be an exact string')
        if not LABEL.match(employee):
            fail('employee must be 1 to 24 lowercase identifier characters')
        if type(rating) is not int:
            raise TypeError('rating must be an exact integer')
        if not 0 <= rating <= 5:
            fail('rating must be 0 to 5')
        if type(improvements) is not int:
            raise TypeError('improvements must be an exact integer')
        if not 0 <= improvements <= 10:
            fail('improvements must be 0 to 10')
        if rating < 2:
            problems.append((i, 'failing'))
        if improvements < 1:
            problems.append((i, 'stagnant'))
        names.add(employee)
    return {'problems': sorted(problems), 'employees': sorted(names), 'total': len(reviews)}
