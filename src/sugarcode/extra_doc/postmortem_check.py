"""Row 638, Post-Mortem: completeness check of a supplied post-mortem.

postmortem_check takes sections, a list or tuple of 0 to 8 unique names from summary, timeline,
impact, root_cause, actions, lessons, followup and appendix; then action_items, a
list or tuple of 0 to 10 (owner, due_day) pairs with owner a string of 1 to 12
characters and due_day a nonbool int from incident_day to 365; incident_day a
nonbool int from 0 to 365; max_days a nonbool int from 1 to 365.
Required sections are summary, timeline, impact, root_cause and actions.
Reported: missing (required names not supplied, in that order), complete (none
missing), late (indexes of items due more than max_days after incident_day),
owners (sorted unique owner names) and ready (complete, at least one action
item and none late).
Caps (checked before any work): the ranges above, in argument order.
NOT_CLAIMED: tracking real action items, blameless review quality, meeting
scheduling, publishing, production readiness.
"""
SCOPE = 'PARTIAL: completeness check of supplied post-mortem parts, no tracking or publishing'
NOT_CLAIMED = ('tracking real action items', 'blameless review quality', 'meeting scheduling',
               'publishing', 'production readiness')

REQUIRED = ('summary', 'timeline', 'impact', 'root_cause', 'actions')
ALLOWED = REQUIRED + ('lessons', 'followup', 'appendix')
MAX_ITEMS = 10


def _int(v, lo, hi, msg):
    if type(v) is not int or not lo <= v <= hi:
        raise ValueError(msg)


def postmortem_check(sections, action_items, incident_day=0, max_days=30):
    if type(sections) not in (list, tuple):
        raise TypeError('sections must be a list or tuple')
    if type(action_items) not in (list, tuple):
        raise TypeError('action_items must be a list or tuple')
    if len(sections) > len(ALLOWED):
        raise ValueError('sections must contain at most 8 entries')
    if len(action_items) > MAX_ITEMS:
        raise ValueError('action_items must contain at most 10 entries')
    _int(incident_day, 0, 365, 'incident_day must be a nonbool integer between 0 and 365')
    _int(max_days, 1, 365, 'max_days must be a nonbool integer between 1 and 365')
    seen = set()
    for s in sections:
        if type(s) is not str or s not in ALLOWED:
            raise ValueError('unknown section name')
        if s in seen:
            raise ValueError('duplicate section name')
        seen.add(s)
    owners = set()
    late = []
    for i, item in enumerate(action_items):
        if type(item) not in (list, tuple) or len(item) != 2:
            raise ValueError('each action item must be an (owner, due_day) pair')
        owner, due = item
        if type(owner) is not str or not 1 <= len(owner) <= 12:
            raise ValueError('owner must be a string of 1 to 12 characters')
        _int(due, incident_day, 365, 'due_day must be a nonbool integer from incident_day to 365')
        owners.add(owner)
        if due - incident_day > max_days:
            late.append(i)
    missing = [r for r in REQUIRED if r not in seen]
    return {
        'missing': missing,
        'complete': not missing,
        'late': late,
        'owners': sorted(owners),
        'ready': not missing and len(action_items) > 0 and not late,
    }
