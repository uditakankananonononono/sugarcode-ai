"""Row 651, Two-Phase Commit: decision rule over supplied participant votes.

two_phase_commit takes votes, a list or tuple of 1 to 8 (participant, vote)
pairs: participant a unique string of 1 to 16 characters, vote one of 'yes',
'no' or 'timeout'. short_circuit is a real bool, default True. The
coordinator asks participants in listed order. With short_circuit it stops
at the first vote that is not 'yes'; otherwise it asks everyone. It commits
only when every participant asked said 'yes' and all were asked, else it
aborts. Reported: decision, asked (names, in order), committed (all names on
commit, else empty), aborted (on abort the asked participants that voted
'yes', in order, since they were prepared) and blocker (the first participant
whose vote was not 'yes', else None).
Checks, in this order: votes type, votes size, short_circuit, then per vote
the pair shape, participant, duplicate participant and vote value.
NOT_CLAIMED: networking, logs, crash recovery, timeouts in real time,
locking, production readiness.
"""
SCOPE = 'PARTIAL: two-phase commit decision over supplied votes, no network or recovery'
NOT_CLAIMED = ('networking', 'logs', 'crash recovery', 'timeouts in real time', 'locking',
               'production readiness')

VOTES = ('yes', 'no', 'timeout')
MAX_VOTES = 8


def two_phase_commit(votes, short_circuit=True):
    if type(votes) not in (list, tuple):
        raise TypeError('votes must be a list or tuple')
    if not 1 <= len(votes) <= MAX_VOTES:
        raise ValueError('votes must contain 1 to 8 entries')
    if type(short_circuit) is not bool:
        raise ValueError('short_circuit must be a bool')
    seen = set()
    for v in votes:
        if type(v) not in (list, tuple) or len(v) != 2:
            raise ValueError('each vote must be a (participant, vote) pair')
        name, vote = v
        if type(name) is not str or not 1 <= len(name) <= 16:
            raise ValueError('participants must be strings of 1 to 16 characters')
        if name in seen:
            raise ValueError('duplicate participant')
        seen.add(name)
        if type(vote) is not str or vote not in VOTES:
            raise ValueError('vote must be yes, no or timeout')
    asked, blocker = [], None
    for name, vote in votes:
        asked.append((name, vote))
        if vote != 'yes' and blocker is None:
            blocker = name
            if short_circuit:
                break
    names = [a[0] for a in asked]
    if blocker is None:
        return {'decision': 'commit', 'asked': names, 'committed': names, 'aborted': [], 'blocker': None}
    return {'decision': 'abort', 'asked': names, 'committed': [],
            'aborted': [a[0] for a in asked if a[1] == 'yes'], 'blocker': blocker}
