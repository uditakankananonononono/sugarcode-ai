"""Row 686, Behavior-Driven Development (PARTIAL: one exact scenario-shape rule): check the step order of a Given/When/Then scenario.

check_scenario(steps) takes steps as a list of (keyword, text): keyword is 'Given', 'When', 'Then', 'And' or 'But', and text a
string of 1 to 80 printable ASCII characters with no leading or trailing space. 'And' and 'But' take the effective keyword of
the step before them. It returns {'effective': the effective keyword of each step, None for an And/But with nothing before
it, 'problems': sorted (index, code)}. Codes:
  (i, 'and_first')     step i is an And/But at position 0 (no keyword to inherit);
  (i, 'out_of_order')  the effective keyword of step i comes earlier in Given, When, Then than the one before it;
  (-1, 'no_when')      no step has the effective keyword When;
  (-1, 'no_then')      no step has the effective keyword Then.
The empty scenario gets (-1, 'no_when') and (-1, 'no_then'). An And/But after an and_first step stays None and is not
reported again.
Caps: 0 to 40 steps.
Order of checks: steps (list type, count, then each in order: tuple type, 2 items, keyword type and value, text type, length
and characters), and only then the analysis.

NOT_CLAIMED: this checks keyword order only. It does not read the text of a step, say that a scenario describes behaviour well, or
run any step. No clinical or wet-lab claim.
"""
KEYWORDS = ('Given', 'When', 'Then', 'And', 'But')
RANK = {k: i for i, k in enumerate(('Given', 'When', 'Then'))}


def check_scenario(steps):
    if type(steps) is not list:
        raise TypeError('steps must be an exact list')
    if len(steps) > 40:
        raise ValueError('step count must be at most 40')
    for s in steps:
        if type(s) is not tuple:
            raise TypeError('each step must be an exact tuple')
        if len(s) != 2:
            raise ValueError('each step must have 2 items')
        if type(s[0]) is not str:
            raise TypeError('keyword must be an exact string')
        if s[0] not in KEYWORDS:
            raise ValueError("keyword must be 'Given', 'When', 'Then', 'And' or 'But'")
        if type(s[1]) is not str:
            raise TypeError('text must be an exact string')
        if not 1 <= len(s[1]) <= 80:
            raise ValueError('text must be 1 to 80 characters')
        if not all(' ' <= c <= '~' for c in s[1]) or s[1][0] == ' ' or s[1][-1] == ' ':
            raise ValueError('text must be printable ASCII with no leading or trailing space')
    effective = []
    problems = []
    for i, (kw, _) in enumerate(steps):
        if kw in RANK:
            eff = kw
        elif i == 0:
            eff = None
            problems.append((0, 'and_first'))
        else:
            eff = effective[-1]
        if eff is not None and effective and effective[-1] is not None and RANK[eff] < RANK[effective[-1]]:
            problems.append((i, 'out_of_order'))
        effective.append(eff)
    if 'When' not in effective:
        problems.append((-1, 'no_when'))
    if 'Then' not in effective:
        problems.append((-1, 'no_then'))
    return {'effective': effective, 'problems': sorted(problems)}
