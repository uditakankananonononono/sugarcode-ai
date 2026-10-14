"""Row 763, Mentalizing: summarizing a supplied sequence of states.

Understands mental states by tracking. Each event is one of 'calm',
'curious', 'anxious', or 'focused'. Reported: the four state counts,
the final state (None when there are no events), and the shifts -
how many adjacent pairs of events differ. Caps (checked before any
work): 0 to 100 events.
NOT_CLAIMED: real mental states, emotion recognition, clinical use,
physiology, prediction, diagnosis, production readiness.
"""
SCOPE = 'PARTIAL: state sequence summarizing over supplied events, no real mentalizing'
NOT_CLAIMED = ('real mental states', 'emotion recognition', 'clinical use',
               'physiology', 'prediction', 'diagnosis', 'production readiness')

MAX_EVENTS = 100
STATES = ('calm', 'curious', 'anxious', 'focused')


def track(events):
    if type(events) not in (list, tuple):
        raise TypeError('events must be a list or tuple')
    if len(events) > MAX_EVENTS:
        raise ValueError('events must contain at most 100 rows')
    for event in events:
        if type(event) is not str or event not in STATES:
            raise ValueError('events must be calm, curious, anxious, or focused')
    counts = {'calm': 0, 'curious': 0, 'anxious': 0, 'focused': 0}
    for event in events:
        counts[event] += 1
    shifts = 0
    for index in range(1, len(events)):
        if events[index] != events[index - 1]:
            shifts += 1
    return {'calm': counts['calm'], 'curious': counts['curious'],
            'anxious': counts['anxious'], 'focused': counts['focused'],
            'final': events[-1] if events else None, 'shifts': shifts}
