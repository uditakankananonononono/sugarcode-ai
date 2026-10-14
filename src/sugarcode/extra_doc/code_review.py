"""Row 690, Code Review (Bounded: one exact merge-gate rule): decide from review records whether a change may merge.

check_review(author, reviews, comments) takes author, a name; reviews, a list of (reviewer, verdict) in time order with verdict
'approve', 'request_changes' or 'comment'; and comments, a list of (comment, severity, resolved) with severity 'blocker', 'major',
'minor' or 'nit' and resolved an exact bool. Only the latest review of each reviewer counts, and the author's own reviews are
ignored. It returns:
  approvals  sorted reviewers whose counted verdict is 'approve';
  blocks     sorted codes from:
             'needs_two_approvals'  fewer than 2 approvals;
             'changes_requested'    some counted verdict is 'request_changes';
             'open_blocking'        some comment with severity blocker or major is not resolved;
  mergeable  True when blocks is empty.
Caps: 0 to 32 reviews, 0 to 32 comments with unique comment names. Names are 1 to 24 lowercase identifier characters.
Order of checks: author (type, shape), reviews (list type, count, then each in order: tuple type, 2 items, reviewer name type and
shape, verdict type and value), comments (list type, count, then each in order: tuple type, 3 items, comment name type and
shape, severity type and value, resolved exact bool), duplicate comment name, and only then the analysis.

NOT_CLAIMED: this applies a gate to supplied records. It does not read the change, judge a review, find defects, or say that a
change is correct. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')
VERDICTS = ('approve', 'request_changes', 'comment')
SEVERITIES = ('blocker', 'major', 'minor', 'nit')


def _name(v):
    if type(v) is not str:
        raise TypeError('name must be an exact string')
    if LABEL.fullmatch(v) is None:
        raise ValueError('name must be 1 to 24 lowercase identifier characters')


def check_review(author, reviews, comments):
    _name(author)
    if type(reviews) is not list:
        raise TypeError('reviews must be an exact list')
    if len(reviews) > 32:
        raise ValueError('review count must be at most 32')
    for r in reviews:
        if type(r) is not tuple:
            raise TypeError('each review must be an exact tuple')
        if len(r) != 2:
            raise ValueError('each review must have 2 items')
        _name(r[0])
        if type(r[1]) is not str:
            raise TypeError('verdict must be an exact string')
        if r[1] not in VERDICTS:
            raise ValueError("verdict must be 'approve', 'request_changes' or 'comment'")
    if type(comments) is not list:
        raise TypeError('comments must be an exact list')
    if len(comments) > 32:
        raise ValueError('comment count must be at most 32')
    for c in comments:
        if type(c) is not tuple:
            raise TypeError('each comment must be an exact tuple')
        if len(c) != 3:
            raise ValueError('each comment must have 3 items')
        _name(c[0])
        if type(c[1]) is not str:
            raise TypeError('severity must be an exact string')
        if c[1] not in SEVERITIES:
            raise ValueError("severity must be 'blocker', 'major', 'minor' or 'nit'")
        if type(c[2]) is not bool:
            raise TypeError('resolved must be an exact bool')
    if len({c[0] for c in comments}) != len(comments):
        raise ValueError('duplicate comment name')
    latest = {}
    for who, verdict in reviews:
        if who != author:
            latest[who] = verdict
    approvals = sorted(w for w, v in latest.items() if v == 'approve')
    blocks = []
    if len(approvals) < 2:
        blocks.append('needs_two_approvals')
    if 'request_changes' in latest.values():
        blocks.append('changes_requested')
    if any(sev in ('blocker', 'major') and not done for _, sev, done in comments):
        blocks.append('open_blocking')
    return {'approvals': approvals, 'blocks': sorted(blocks), 'mergeable': not blocks}
