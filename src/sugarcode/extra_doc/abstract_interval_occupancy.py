"""Row 1190: Quarantine Management.

PARTIAL: counts inclusive supplied abstract intervals containing a supplied
integer point. Caps are module-local choices, not health standards.
No confinement decisions, exposure assessment or medical advice.
"""
NOT_CLAIMED = ('confinement_decisions', 'exposure_assessment', 'medical_advice')


def occupancy(intervals, point):
    if type(intervals) is not tuple or not 0 <= len(intervals) <= 20:
        raise ValueError('intervals: tuple of 0 to 20 pairs required')
    for i,row in enumerate(intervals):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'intervals[{i}]: pair (start, end) required')
        for j,value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 1000:
                raise ValueError(f'intervals[{i}][{j}]: whole number 0 to 1000 required')
        if row[0] > row[1]:
            raise ValueError(f'intervals[{i}]: start must not exceed end')
    if type(point) is not int or not 0 <= point <= 1000:
        raise ValueError('point: whole number 0 to 1000 required')
    active = tuple(i for i,(start,end) in enumerate(intervals) if start <= point <= end)
    return {'abstract_interval_occupancy_validated': False, 'not_claimed': NOT_CLAIMED,
            'active_positions': active, 'active_count': len(active), 'unoccupied': not active}
