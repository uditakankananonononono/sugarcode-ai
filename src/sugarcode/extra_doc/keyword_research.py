"""Row 410, Keyword Research (PARTIAL: one exact list rule): check a supplied keyword list for repeats and coverage.

check_keywords(terms) takes terms as a list of 0 to 50 exact strings of 1 to 40 characters. A term's folded form is its
words lowercased and joined by single spaces. The rules, applied to each term i (0-based), are:
  the term differs from its folded form (odd case or spacing), else (i, 'messy');
  a folded form already listed by an earlier term, else (i, 'repeat');
  fewer than 3 characters, else (i, 'thin');
  every word already inside one earlier term's word set, with fewer words than that term, else (i, 'covered') -
  reported once per term, against the earliest covering term.
One term can break several rules; all are reported. It returns {'problems': sorted (index, code), 'folded': sorted
distinct folded forms, 'words': the number of distinct words across all folded forms, 'total': the term count}.
Order of checks: terms (list type, count, then each in order: string type, length bounds), and only then the rules.

NOT_CLAIMED: this tidies a supplied list. It does not say the keywords get searched, that coverage is bad, or that any
of them ranks. No clinical or wet-lab claim.
"""


def _fold(term):
    return ' '.join(term.lower().split())


def check_keywords(terms):
    if type(terms) is not list:
        raise TypeError('terms must be an exact list')
    if len(terms) > 50:
        raise ValueError('term count must be at most 50')
    for t in terms:
        if type(t) is not str:
            raise TypeError('each term must be an exact string')
        if not 1 <= len(t) <= 40:
            raise ValueError('term length must be 1 to 40 characters')
    problems = []
    folded = []
    seen = set()
    for i, t in enumerate(terms):
        f = _fold(t)
        if t != f:
            problems.append((i, 'messy'))
        if f in seen:
            problems.append((i, 'repeat'))
        seen.add(f)
        if len(t) < 3:
            problems.append((i, 'thin'))
        words = set(f.split())
        for g in folded:
            earlier = set(g.split())
            if words and words < earlier:
                problems.append((i, 'covered'))
                break
        folded.append(f)
    return {'problems': sorted(problems), 'folded': sorted(seen),
            'words': len({w for f in seen for w in f.split()}), 'total': len(terms)}
