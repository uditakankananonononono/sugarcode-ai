"""Row 1890, Title: Neurolinguistics

map_activation(rows): rows are (region, task, signal) triples;
region and task strings of 1 to 16 characters; signal a nonbool
integer between 1 and 9. Caps (checked before any work): 1 to
60 rows. Reported: the total row count, for each region the
number of tasks activating it at signal at least 5, the hot
regions (activated by at least 3 tasks, sorted alphabetically),
the cold regions (activated by none, sorted alphabetically),
for each region the total signal, and the busiest region (the
largest total signal, first supplied on ties).

SCOPE: PARTIAL: activation mapping over supplied signals
NOT_CLAIMED: brain imaging, Broca's area, lesion studies,
neural substrates, production readiness.
"""

SCOPE = 'PARTIAL: activation mapping over supplied signals'
NOT_CLAIMED = ('brain imaging', "Broca's area", 'lesion studies',
               'neural substrates', 'production readiness')


def map_activation(rows):
    if type(rows) not in (list, tuple):
        raise TypeError('rows must be a list or tuple')
    if not 1 <= len(rows) <= 60:
        raise ValueError('rows must contain between 1 and 60 entries')
    for i, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(f'row {i}: expected a (region, task, signal) triple')
        if len(row) != 3:
            raise ValueError(f'row {i}: expected 3 fields, got {len(row)}')
        region, task, signal = row
        if type(region) is not str or not 1 <= len(region) <= 16:
            raise ValueError(f'row {i}: region must be a string of 1 to 16 characters')
        if type(task) is not str or not 1 <= len(task) <= 16:
            raise ValueError(f'row {i}: task must be a string of 1 to 16 characters')
        if type(signal) is not int or not 1 <= signal <= 9:
            raise ValueError(f'row {i}: signal must be a nonbool integer between 1 and 9')
    activators = {}
    signal_sum = {}
    for region, task, signal in rows:
        if region not in activators:
            activators[region] = {}
            signal_sum[region] = 0
        if signal >= 5:
            activators[region][task] = True
        signal_sum[region] += signal
    engaged = {}
    for region in activators:
        engaged[region] = len(activators[region])
    hot = sorted(region for region in engaged if engaged[region] >= 3)
    cold = sorted(region for region in engaged if engaged[region] == 0)
    busiest = None
    for region in signal_sum:
        if busiest is None or signal_sum[region] > signal_sum[busiest]:
            busiest = region
    return {'total': len(rows),
            'engaged': engaged,
            'hot': hot,
            'cold': cold,
            'signal': signal_sum,
            'busiest': busiest}
