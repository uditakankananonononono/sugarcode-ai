"""Row 831, Formative Assessment - Assesses for learning: topic status from checks.

formative_checks takes checks, a list or tuple of 0 to max_checks (topic,
score) pairs in time order, pass_mark, a nonbool int from 1 to 5 (default 3),
and max_checks, a nonbool int from 1 to 20 (default 8). A topic is a string
of 1 to 12 characters. score is a nonbool int from 0 to 5.
For each topic, in order of first appearance, the latest score decides: the
status is 'reteach' when the latest score is below pass_mark, else 'on_track'.
Returns topics (one (name, count, latest, status) tuple per topic), reteach
(names with status reteach, in the same order) and all_on_track (no topic
needs reteach; True with no checks).
Checks, in this order: pass_mark, max_checks, checks type, checks size, each
pair (shape, topic, score).
NOT_CLAIMED: real learning, test quality, student effort, grading fairness,
production readiness.
"""
SCOPE = 'PARTIAL: latest-score status per topic of supplied checks, no learner is assessed'
NOT_CLAIMED = ('real learning', 'test quality', 'student effort',
               'grading fairness', 'production readiness')


def formative_checks(checks, pass_mark=3, max_checks=8):
    if type(pass_mark) is not int or not 1 <= pass_mark <= 5:
        raise ValueError('pass_mark must be a nonbool integer between 1 and 5')
    if type(max_checks) is not int or not 1 <= max_checks <= 20:
        raise ValueError('max_checks must be a nonbool integer between 1 and 20')
    if type(checks) not in (list, tuple):
        raise TypeError('checks must be a list or tuple')
    if len(checks) > max_checks:
        raise ValueError('checks must contain at most max_checks entries')
    state = {}
    for c in checks:
        if type(c) not in (list, tuple) or len(c) != 2:
            raise ValueError('each check must be a (topic, score) pair')
        topic, score = c
        if type(topic) is not str or not 1 <= len(topic) <= 12:
            raise ValueError('each topic must be a string of 1 to 12 characters')
        if type(score) is not int or not 0 <= score <= 5:
            raise ValueError('score must be a nonbool integer between 0 and 5')
        n, _ = state.get(topic, (0, 0))
        state[topic] = (n + 1, score)
    topics = []
    for name, (n, last) in state.items():
        topics.append((name, n, last, 'reteach' if last < pass_mark else 'on_track'))
    redo = [t[0] for t in topics if t[3] == 'reteach']
    return {'topics': topics, 'reteach': redo, 'all_on_track': not redo}
