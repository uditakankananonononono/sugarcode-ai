"""Row 1193, Medication Adherence.

PARTIAL: supplied identifier reconciliation only. No verification that any
medication was taken, prescribed correctly or safe. No medical advice.

reconcile(schedule, logs) accepts exact list/tuple containers. Schedule contains
1..64 exact pairs (person, event); the pairs must be unique. Logs contains
0..128 pairs of the same form and may repeat. Identifiers are exact strings
of 1..24 ASCII letters, digits or underscore. At most16 people across both
inputs. Validation processes all schedule rows, then logs, then person cap.
Return label-sorted per-person rows (person, scheduled, logged_scheduled,
missing), sorted missing scheduled pairs, sorted unexpected unique log pairs,
and repeated log pairs. Repeated means a pair occurs at least twice, reported
once. People present only in logs get zero schedule counts. Inputs unchanged.
"""
SCOPE = 'PARTIAL: supplied schedule/log IDs only; no medication-taking assessment'
NOT_CLAIMED = (
    'does not verify medication was taken',
    'does not validate prescriptions, doses or timing',
    'does not estimate adherence or health outcomes',
    'does not recommend medication changes',
)


def _label(value):
    if type(value) is not str:
        raise TypeError('identifier must be an exact string')
    if not 1 <= len(value) <= 24 or not all(
        c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_'
        for c in value
    ):
        raise ValueError('identifier must be 1..24 ASCII word characters')


def _pairs(rows, name, minimum, maximum):
    if type(rows) not in (list, tuple):
        raise TypeError(name + ' must be an exact list or tuple')
    if not minimum <= len(rows) <= maximum:
        raise ValueError(name + ' count outside declared range')
    result = []
    for row in rows:
        if type(row) not in (list, tuple):
            raise TypeError(name + ' row must be an exact list or tuple')
        if len(row) != 2:
            raise ValueError(name + ' row must have two identifiers')
        _label(row[0])
        _label(row[1])
        result.append(tuple(row))
    return result


def reconcile(schedule, logs):
    planned = _pairs(schedule, 'schedule', 1, 64)
    if len(set(planned)) != len(planned):
        raise ValueError('scheduled pairs must be unique')
    recorded = _pairs(logs, 'logs', 0, 128)
    people = {p for p, _ in planned + recorded}
    if len(people) > 16:
        raise ValueError('at most16 people allowed')
    scheduled = set(planned)
    logged = set(recorded)
    frequency = {}
    for pair in recorded:
        frequency[pair] = frequency.get(pair, 0) + 1
    rows = []
    for person in sorted(people):
        expected = {e for p, e in scheduled if p == person}
        found = {e for p, e in logged if p == person}
        rows.append((person, len(expected), len(expected & found), len(expected - found)))
    return {
        'people': rows,
        'missing': sorted(scheduled - logged),
        'unexpected': sorted(logged - scheduled),
        'repeated': sorted(pair for pair, count in frequency.items() if count >= 2),
        'scope': SCOPE,
        'not_claimed': list(NOT_CLAIMED),
    }
