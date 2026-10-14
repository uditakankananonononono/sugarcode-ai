"""Row 416, Public Relations (PARTIAL: one exact triage rule): check a supplied mention list against fixed reach bars.

check_mentions(mentions) takes mentions as a list of 0 to 40 tuples (source, sentiment, reach): source 1 to 24
lowercase identifier characters, sentiment one of 'positive', 'neutral', 'negative' (exact strings), reach an exact
int from 0 to 1000000. The rules, applied to each mention i (0-based), are:
  negative sentiment with reach 10000 or more, else (i, 'crisis');
  negative sentiment with reach 1000 or more (and under 10000), else (i, 'watch');
  the same (source, sentiment) pair as an earlier mention, else (i, 'repeat').
One mention can break several rules; all are reported. It returns {'problems': sorted (index, code), 'net': the
positive count minus the negative count, 'reach': the summed reach, 'total': the mention count}.
Order of checks: mentions (list type, count, then each in order: tuple type, 3 items, source type and shape, sentiment
type and value, reach type and range), and only then the rules.

NOT_CLAIMED: this sorts a supplied table against fixed bars. It does not say the reputation is good, that 10000 is the
right crisis bar, or that any mention is real. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
SENTIMENTS = frozenset({'positive', 'neutral', 'negative'})


def check_mentions(mentions):
    if type(mentions) is not list:
        raise TypeError('mentions must be an exact list')
    if len(mentions) > 40:
        raise ValueError('mention count must be at most 40')
    for m in mentions:
        if type(m) is not tuple:
            raise TypeError('each mention must be an exact tuple')
        if len(m) != 3:
            raise ValueError('each mention must have 3 items')
        if type(m[0]) is not str:
            raise TypeError('source must be an exact string')
        if LABEL.fullmatch(m[0]) is None:
            raise ValueError('source must be 1 to 24 lowercase identifier characters')
        if type(m[1]) is not str:
            raise TypeError('sentiment must be an exact string')
        if m[1] not in SENTIMENTS:
            raise ValueError('sentiment must be one of: negative, neutral, positive')
        if type(m[2]) is not int:
            raise TypeError('reach must be an exact int')
        if not 0 <= m[2] <= 1000000:
            raise ValueError('reach must be between 0 and 1000000')
    problems = []
    seen_pairs = set()
    net = 0
    reach = 0
    for i, (source, sentiment, r) in enumerate(mentions):
        if sentiment == 'negative':
            net -= 1
            if r >= 10000:
                problems.append((i, 'crisis'))
            elif r >= 1000:
                problems.append((i, 'watch'))
        elif sentiment == 'positive':
            net += 1
        if (source, sentiment) in seen_pairs:
            problems.append((i, 'repeat'))
        seen_pairs.add((source, sentiment))
        reach += r
    return {'problems': sorted(problems), 'net': net, 'reach': reach, 'total': len(mentions)}
