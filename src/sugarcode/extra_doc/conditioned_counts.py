"""Row 1083: Selective Inference - Conditional inference.

PARTIAL: filters supplied (group, count) pairs by a supplied integer
group and sums the selected counts. No conditional inference,
selection adjustment or statistical validity. Caps of 1-30 pairs,
groups 0-10 and counts 0-1000 are this module's own choices.
"""
MAX_ROWS = 30
MAX_GROUP = 10
MAX_COUNT = 1000
NOT_CLAIMED = ('conditional_inference', 'selection_adjustment', 'statistical_validity')


def condition(rows, group):
    if type(rows) is not tuple or not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError('rows: tuple of 1 to 30 pairs required')
    for i,row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'rows[{i}]: pair (group, count) required')
        for name,value,cap in (('group',row[0],MAX_GROUP),('count',row[1],MAX_COUNT)):
            if type(value) is not int or not 0 <= value <= cap:
                raise ValueError(f'rows[{i}].{name}: whole number 0 to {cap} required')
    if type(group) is not int or not 0 <= group <= MAX_GROUP:
        raise ValueError('group: whole number 0 to 10 required')
    positions = tuple(i for i in range(len(rows)) if rows[i][0] == group)
    total = sum(rows[i][1] for i in positions)
    return {'conditioned_counts_validated': False, 'not_claimed': NOT_CLAIMED,
            'positions': positions, 'count_total': total, 'selected_count': len(positions)}
