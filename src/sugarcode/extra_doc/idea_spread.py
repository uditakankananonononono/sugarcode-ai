"""Row 866, Divergent Thinking - Generates many ideas: how widely ideas spread.

idea_spread takes ideas, a list or tuple of 1 to 10 (idea, category) tuples,
and min_categories, a nonbool int from 1 to 6 (default 3). idea and category
are printable ASCII strings of 1 to 12 characters (control characters are
refused). Ideas are distinct across entries.
Returns fluency (how many ideas), flexibility (how many different categories),
by_category (a list of (category, count) with the biggest count first and ties
by category), top_percent (the biggest count as a percent of fluency, rounded
down), balanced (True when no category holds more than half of the ideas,
compared exactly) and diverse (True when flexibility is at least
min_categories).
Checks, in this order: min_categories, ideas type, ideas size, each entry
(shape, idea, category), distinct ideas.
NOT_CLAIMED: real divergent thinking, quality of ideas, originality, learner
creativity, production readiness.
"""

SCOPE = 'PARTIAL: counts supplied ideas and their categories, no thinking is assessed'
NOT_CLAIMED = ('real divergent thinking', 'quality of ideas', 'originality',
               'learner creativity', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def idea_spread(ideas, min_categories=3):
    if type(min_categories) is not int or not 1 <= min_categories <= 6:
        raise ValueError('min_categories must be a nonbool integer between 1 and 6')
    if type(ideas) not in (list, tuple):
        raise TypeError('ideas must be a list or tuple')
    if not 1 <= len(ideas) <= 10:
        raise ValueError('ideas must contain 1 to 10 entries')
    rows = []
    for e in ideas:
        if type(e) not in (list, tuple) or len(e) != 2:
            raise ValueError('each entry must be an (idea, category) tuple')
        idea, category = e
        if not _label(idea):
            raise ValueError('each idea must be a printable ASCII string of 1 to 12 characters')
        if not _label(category):
            raise ValueError('each category must be a printable ASCII string of 1 to 12 characters')
        rows.append((idea, category))
    if len({r[0] for r in rows}) != len(rows):
        raise ValueError('ideas must be distinct')
    counts = {}
    for _, category in rows:
        counts[category] = counts.get(category, 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    top = ordered[0][1]
    return {'fluency': len(rows), 'flexibility': len(counts), 'by_category': ordered,
            'top_percent': top * 100 // len(rows), 'balanced': top * 2 <= len(rows),
            'diverse': len(counts) >= min_categories}
