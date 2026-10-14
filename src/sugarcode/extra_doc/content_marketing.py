"""Row 414, Content Marketing (Bounded: one exact mapping rule): check a supplied asset list for funnel coverage.

check_assets(assets) takes assets as a list of 0 to 30 tuples (title, stage, fmt): title an exact string of 1 to 100
characters, stage one of 'awareness', 'consideration', 'decision' (exact strings), fmt one of 'blog', 'video', 'guide',
'webinar', 'case_study' (exact strings). The rules, applied to each asset i (0-based), are:
  the same title as an earlier asset, else (i, 'repeat');
  a title longer than 70 characters, else (i, 'title_long');
  a (stage, fmt) pair in the fixed mismatch table {('awareness', 'case_study'), ('decision', 'blog')}, else
  (i, 'mismatched').
After all assets, any stage with no asset is reported in 'gaps'. It returns {'problems': sorted (index, code),
'gaps': sorted stages with no assets, 'by_stage': {stage: count} for the stages used, keyed in sorted order, 'total':
the asset count}.
Order of checks: assets (list type, count, then each in order: tuple type, 3 items, title type and length, stage type
and value, fmt type and value), and only then the rules.

NOT_CLAIMED: this checks a supplied list against fixed tables. It does not say the content is valuable, that the
mismatch table fits every funnel, or that coverage converts. No clinical or wet-lab claim.
"""

STAGES = frozenset({'awareness', 'consideration', 'decision'})
FORMATS = frozenset({'blog', 'video', 'guide', 'webinar', 'case_study'})
MISMATCH = frozenset({('awareness', 'case_study'), ('decision', 'blog')})


def check_assets(assets):
    if type(assets) is not list:
        raise TypeError('assets must be an exact list')
    if len(assets) > 30:
        raise ValueError('asset count must be at most 30')
    for a in assets:
        if type(a) is not tuple:
            raise TypeError('each asset must be an exact tuple')
        if len(a) != 3:
            raise ValueError('each asset must have 3 items')
        if type(a[0]) is not str:
            raise TypeError('title must be an exact string')
        if not 1 <= len(a[0]) <= 100:
            raise ValueError('title length must be 1 to 100 characters')
        if type(a[1]) is not str:
            raise TypeError('stage must be an exact string')
        if a[1] not in STAGES:
            raise ValueError('stage must be one of: awareness, consideration, decision')
        if type(a[2]) is not str:
            raise TypeError('fmt must be an exact string')
        if a[2] not in FORMATS:
            raise ValueError('fmt must be one of: blog, case_study, guide, video, webinar')
    problems = []
    seen_titles = set()
    by_stage = {}
    for i, (title, stage, fmt) in enumerate(assets):
        if title in seen_titles:
            problems.append((i, 'repeat'))
        seen_titles.add(title)
        if len(title) > 70:
            problems.append((i, 'title_long'))
        if (stage, fmt) in MISMATCH:
            problems.append((i, 'mismatched'))
        by_stage[stage] = by_stage.get(stage, 0) + 1
    gaps = sorted(STAGES - set(by_stage))
    return {'problems': sorted(problems), 'gaps': gaps,
            'by_stage': dict(sorted(by_stage.items())), 'total': len(assets)}
