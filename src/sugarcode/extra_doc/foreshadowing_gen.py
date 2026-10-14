"""Row 266 v2, Foreshadowing Placement: choose and place hints optimally (exact).

Uses foreshadowing.py for its certificate (needs that module: the v1 patch). The
caller supplies the scene count n, the reveal scene, a pool of candidate hints
given by their salience (chance a reader notices; independent), and caps:
max_salience (every used hint must be at most this loud), min_notice (the used
hints together must be noticed with at least this probability) and max_gap (the
longest silent stretch in scenes, counted from scene 0 to the first hint, between
hints, and from the last hint to the reveal).
Search is exact over every subset of the pool. A subset is feasible when all its
saliences are within max_salience, it has at most reveal - 1 hints (one per scene,
scenes 1 to reveal - 1), 1 - prod(1 - s) >= min_notice, and the best possible
placement of m hints reaches a longest gap of ceil(reveal / (m + 1)) <= max_gap
(pigeonhole: that is the least possible longest gap for m hints).
Best subset = lowest loudest hint (maximal subtlety = 1 - max salience, the empty
set counts as 0), then fewest hints, then lowest notice probability, then
lexicographically smallest index list. Placement of the m hints: the m + 1 gaps are
as even as possible, the longer gaps last, so positions are the prefix sums; chosen
hints go to those scenes in index order.
Certificate: the plan re-scored by foreshadowing.place_hints (valid, subtle, gaps),
the number of subsets examined, and max_notice_within_cap (best notice reachable
using every hint within the cap, within the scene limit), which explains an
infeasible answer.
Caps: 1 to 64 scenes, 0 to 8 pool hints, max_gap 1 to n_scenes, 32-bit rationals,
thresholds and saliences as in foreshadowing.py. Order of checks: types and counts
first, then conversion and range checks, and only then the search.

NOT_CLAIMED: this optimises numbers the caller supplies. It writes no hint text, does
not know whether a hint is actually subtle to a real reader, and renders nothing
visual. Creative quality is not claimed; the independence of readers noticing hints
is a modelling assumption. No clinical or wet-lab claim.
"""
from fractions import Fraction
from itertools import combinations

from sugarcode.extra_doc.foreshadowing import MAX_HINTS, MAX_SCENES, _q, place_hints


def _positions(reveal, m):
    base, extra = divmod(reveal, m + 1)
    gaps = [base] * (m + 1 - extra) + [base + 1] * extra
    pos, total = [], 0
    for g in gaps[:-1]:
        total += g
        pos.append(total)
    return pos


def generate_hint_plan(n_scenes, reveal, pool, max_salience, min_notice, max_gap):
    if type(n_scenes) is not int or type(reveal) is not int or type(max_gap) is not int:
        raise TypeError('n_scenes, reveal and max_gap must be nonbool ints')
    if not 1 <= n_scenes <= MAX_SCENES:
        raise ValueError('n_scenes must be between 1 and 64')
    if not 1 <= reveal <= n_scenes:
        raise ValueError('reveal must be between 1 and n_scenes')
    if not 1 <= max_gap <= n_scenes:
        raise ValueError('max_gap must be between 1 and n_scenes')
    if type(pool) not in (list, tuple):
        raise TypeError('pool must be a list or tuple of saliences')
    if len(pool) > MAX_HINTS:
        raise ValueError('at most 8 pool hints')
    sal = [_q(v) for v in pool]
    ms, mn = _q(max_salience), _q(min_notice)
    if any(not 0 < s <= 1 for s in sal):
        raise ValueError('salience must be in (0, 1]')
    if not (0 <= ms <= 1 and 0 <= mn <= 1):
        raise ValueError('thresholds must be in [0, 1]')
    best, examined = None, 0
    usable = [i for i, s in enumerate(sal) if s <= ms]
    room = reveal - 1
    for size in range(0, len(sal) + 1):
        for idx in combinations(range(len(sal)), size):
            examined += 1
            if size > room or any(sal[i] > ms for i in idx):
                continue
            if -(-reveal // (size + 1)) > max_gap:
                continue
            miss = Fraction(1)
            for i in idx:
                miss *= 1 - sal[i]
            notice = 1 - miss
            if notice < mn:
                continue
            key = (max((sal[i] for i in idx), default=Fraction(0)), size, notice, idx)
            if best is None or key < best:
                best = key
    cap_miss = Fraction(1)
    for i in sorted(usable, key=lambda i: -sal[i])[:room]:
        cap_miss *= 1 - sal[i]
    out = {'feasible': best is not None, 'chosen': None, 'hints': None, 'check': None,
           'examined': examined, 'max_notice_within_cap': 1 - cap_miss}
    if best is not None:
        idx = list(best[3])
        scenes = _positions(reveal, len(idx))
        hints = [(scenes[k], sal[idx[k]]) for k in range(len(idx))]
        out['chosen'] = idx
        out['hints'] = hints
        out['check'] = place_hints(n_scenes, reveal, hints, max_salience, min_notice)
    return out
