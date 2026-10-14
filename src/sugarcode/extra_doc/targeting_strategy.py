"""Row 401, Targeting Strategy (Bounded: one exact table rule): check supplied segments against fixed targeting floors.

check_targets(segments) takes segments as a list of 0 to 12 tuples (name, size, fit): name 1 to 24 lowercase identifier
characters, size an exact int 1 to 1000000, fit an exact int 0 to 100. The rules, applied to each segment i (0-based):
  size below 100, else (i, 'too_small');
  fit below 60, else (i, 'low_fit');
  a name already used by an earlier segment, else (i, 'same_name').
One segment can break several rules; all are reported. A segment is eligible when it breaks none. It returns
{'problems': sorted (index, code), 'scores': size*fit per segment in input order, 'targets': names of eligible segments
ordered by descending score then input index, 'total_size': sum of all sizes}.
Order of checks: segments (list type, count, then each in order: tuple type, 3 items, name type and shape, size type
and range, fit type and range), and only then the rules.

NOT_CLAIMED: this checks a supplied table. It does not say the floors fit any market, that the fit numbers are measured,
or that choosing these targets helps. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def _int(v, lo, hi, what):
    if type(v) is not int:
        raise TypeError(what + ' must be an exact int')
    if not lo <= v <= hi:
        raise ValueError(what + ' must be %d to %d' % (lo, hi))


def check_targets(segments):
    if type(segments) is not list:
        raise TypeError('segments must be an exact list')
    if len(segments) > 12:
        raise ValueError('segment count must be at most 12')
    for s in segments:
        if type(s) is not tuple:
            raise TypeError('each segment must be an exact tuple')
        if len(s) != 3:
            raise ValueError('each segment must have 3 items')
        name, size, fit = s
        if type(name) is not str:
            raise TypeError('name must be an exact string')
        if LABEL.fullmatch(name) is None:
            raise ValueError('name must be 1 to 24 lowercase identifier characters')
        _int(size, 1, 1000000, 'size')
        _int(fit, 0, 100, 'fit')
    problems, seen, scores, ok = [], set(), [], []
    for i, (name, size, fit) in enumerate(segments):
        bad = False
        if size < 100:
            problems.append((i, 'too_small'))
            bad = True
        if fit < 60:
            problems.append((i, 'low_fit'))
            bad = True
        if name in seen:
            problems.append((i, 'same_name'))
            bad = True
        seen.add(name)
        scores.append(size * fit)
        if not bad:
            ok.append(i)
    ok.sort(key=lambda i: (-scores[i], i))
    return {'problems': sorted(problems), 'scores': scores,
            'targets': [segments[i][0] for i in ok], 'total_size': sum(s[1] for s in segments)}
