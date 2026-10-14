"""Row 415, Thought Leadership (Bounded: one exact evidence rule): check supplied pieces for unsupported claims.

check_pieces(pieces) takes pieces as a list of 0 to 20 tuples (title, claims): title an exact string of 1 to 100
characters, claims a list of 0 to 5 exact strings of 1 to 120 characters (the piece's claims of expertise). A claim's
folded form is its words lowercased and joined by single spaces. The rules, applied to each piece i (0-based), are:
  no claims at all, else (i, 'no_evidence');
  any claim with no digit 0-9 in it, else (i, 'unfounded') - reported once per piece;
  any claim whose folded form contains 'world-class' or 'best-in-class', else (i, 'puffery') - reported once per piece;
  the same title as an earlier piece, else (i, 'repeat').
One piece can break several rules; all are reported. It returns {'problems': sorted (index, code), 'claims': the total
claim count, 'total': the piece count}.
Order of checks: pieces (list type, count, then each in order: tuple type, 2 items, title type and length, claims list
type, claim count, then each claim in order: type and length), and only then the rules.

NOT_CLAIMED: this checks supplied text for digits and two fixed phrases. It does not say the claims are true, that
numbers prove expertise, or that anyone was persuaded. No clinical or wet-lab claim.
"""

PUFFERY = ('world-class', 'best-in-class')


def check_pieces(pieces):
    if type(pieces) is not list:
        raise TypeError('pieces must be an exact list')
    if len(pieces) > 20:
        raise ValueError('piece count must be at most 20')
    for p in pieces:
        if type(p) is not tuple:
            raise TypeError('each piece must be an exact tuple')
        if len(p) != 2:
            raise ValueError('each piece must have 2 items')
        if type(p[0]) is not str:
            raise TypeError('title must be an exact string')
        if not 1 <= len(p[0]) <= 100:
            raise ValueError('title length must be 1 to 100 characters')
        if type(p[1]) is not list:
            raise TypeError('claims must be an exact list')
        if len(p[1]) > 5:
            raise ValueError('claim count must be at most 5')
        for c in p[1]:
            if type(c) is not str:
                raise TypeError('each claim must be an exact string')
            if not 1 <= len(c) <= 120:
                raise ValueError('claim length must be 1 to 120 characters')
    problems = []
    seen_titles = set()
    claims = 0
    for i, (title, claim_list) in enumerate(pieces):
        if not claim_list:
            problems.append((i, 'no_evidence'))
        if any(not any('0' <= ch <= '9' for ch in c) for c in claim_list):
            problems.append((i, 'unfounded'))
        if any(p in ' '.join(c.lower().split()) for c in claim_list for p in PUFFERY):
            problems.append((i, 'puffery'))
        if title in seen_titles:
            problems.append((i, 'repeat'))
        seen_titles.add(title)
        claims += len(claim_list)
    return {'problems': sorted(problems), 'claims': claims, 'total': len(pieces)}
