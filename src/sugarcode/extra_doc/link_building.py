"""Row 411, Link Building (PARTIAL: one exact link-table rule): check a supplied backlink list.

check_links(links) takes links as a list of 0 to 30 tuples (source, target, anchor): source and target 1 to 24
lowercase identifier characters (site slugs), anchor an exact string of 1 to 80 characters. The rules, applied to each
link i (0-based), are:
  source equals target, else (i, 'self_link');
  the same (source, target) pair as an earlier link, else (i, 'repeat');
  an anchor longer than 60 characters, else (i, 'anchor_long');
  an anchor whose words lowercased and joined is one of 'click here', 'here', 'link', 'read more', else
  (i, 'thin_anchor').
One link can break several rules; all are reported. It returns {'problems': sorted (index, code), 'targets': {target:
the number of distinct sources pointing to it} for the targets used, keyed in sorted order, 'total': the link count}.
Order of checks: links (list type, count, then each in order: tuple type, 3 items, source type and shape, target type
and shape, anchor type and length), and only then the rules.

NOT_CLAIMED: this checks a supplied table. It does not say the links exist, that thin anchors hurt, or that any link
passes value. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
THIN = frozenset({'click here', 'here', 'link', 'read more'})


def _name(v, what):
    if type(v) is not str:
        raise TypeError(what + ' must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError(what + ' must be 1 to 24 lowercase identifier characters')


def check_links(links):
    if type(links) is not list:
        raise TypeError('links must be an exact list')
    if len(links) > 30:
        raise ValueError('link count must be at most 30')
    for k in links:
        if type(k) is not tuple:
            raise TypeError('each link must be an exact tuple')
        if len(k) != 3:
            raise ValueError('each link must have 3 items')
        _name(k[0], 'source')
        _name(k[1], 'target')
        if type(k[2]) is not str:
            raise TypeError('anchor must be an exact string')
        if not 1 <= len(k[2]) <= 80:
            raise ValueError('anchor length must be 1 to 80 characters')
    problems = []
    seen_pairs = set()
    sources_by_target = {}
    for i, (source, target, anchor) in enumerate(links):
        if source == target:
            problems.append((i, 'self_link'))
        if (source, target) in seen_pairs:
            problems.append((i, 'repeat'))
        seen_pairs.add((source, target))
        if len(anchor) > 60:
            problems.append((i, 'anchor_long'))
        if ' '.join(anchor.lower().split()) in THIN:
            problems.append((i, 'thin_anchor'))
        sources_by_target.setdefault(target, set()).add(source)
    return {'problems': sorted(problems),
            'targets': {t: len(sources_by_target[t]) for t in sorted(sources_by_target)}, 'total': len(links)}
