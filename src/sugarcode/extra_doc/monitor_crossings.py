"""Row 1138, Anesthesia Monitoring.

monitor_crossings compares supplied before x and after y around baseline.
An up crossing means x<baseline<=y; down means y<baseline<=x. A sample
already equal to baseline is on the upper side. Returns crossings as
(label,'up'/'down') in caller order, up/down as direction counts. No live
anesthesia signals, clinical alarm or patient-safety judgment is implemented.
Inputs: rows is an exact list or tuple of 1 to 8 entries. Each entry is an
exact list or tuple (label, x, y). label is an exact printable ASCII str
of 1 to 12 characters, unique across rows. x and y are exact ints from
0 to 100; bool and all subclasses are refused.
baseline defaults to 50, an exact int from 0 to 100.
Validation order: rows type, rows size, baseline, then each row in input
order (shape, label, x, y), then duplicate labels.
NOT_CLAIMED: anesthesia monitoring, clinical alarms, patient safety, signal provenance, production readiness.
"""

SCOPE = 'PARTIAL: records supplied two-channel crossing directions around a fixed numeric baseline'
NOT_CLAIMED = ('anesthesia monitoring', 'clinical alarms', 'patient safety', 'signal provenance', 'production readiness')


def _label(x):
    return type(x) is str and x.isascii() and x.isprintable() and 1 <= len(x) <= 12


def monitor_crossings(rows, baseline=50):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 8:
        raise ValueError('rows must contain 1 to 8 entries')
    if type(baseline) is not int or not 0 <= baseline <= 100:
        raise ValueError('baseline must be a nonbool integer between 0 and 100')
    clean = []
    for row in rows:
        if type(row) not in (list, tuple) or len(row) != 3:
            raise ValueError('each row must be a (label, x, y) triple')
        label, x, y = row
        if not _label(label):
            raise ValueError('label must be a printable ASCII string of 1 to 12 characters')
        if type(x) is not int or not 0 <= x <= 100:
            raise ValueError('x must be a nonbool integer between 0 and 100')
        if type(y) is not int or not 0 <= y <= 100:
            raise ValueError('y must be a nonbool integer between 0 and 100')
        clean.append((label, x, y))
    if len({r[0] for r in clean}) != len(clean):
        raise ValueError('labels must be distinct')
    crossings = []
    for n, before, after in clean:
        if before < baseline <= after:
            crossings.append((n, 'up'))
        elif after < baseline <= before:
            crossings.append((n, 'down'))
    return {'crossings': crossings, 'up': sum(d == 'up' for n, d in crossings),
            'down': sum(d == 'down' for n, d in crossings)}
