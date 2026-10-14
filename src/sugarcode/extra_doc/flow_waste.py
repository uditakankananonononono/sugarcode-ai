"""Row 459: Lean Manufacturing - Eliminates waste.

PARTIAL: sums supplied work/wait times across sequential stages and
checks the wait share against a supplied percent, with exact integer
comparison. No waste elimination, real production model or lean advice.
Caps of 1-20 stages, 1-1000 work units, 0-1000 wait units, and a
0-100 percent wait-share limit are this module's own choices.
"""
MAX_STAGES = 20
MAX_TIME = 1000
NOT_CLAIMED = ('waste_elimination', 'production_model', 'lean_advice')


def waste(stages, wait_limit):
    if type(stages) is not tuple or not 1 <= len(stages) <= MAX_STAGES:
        raise ValueError('stages: tuple of 1 to 20 pairs required')
    for i,row in enumerate(stages):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'stages[{i}]: pair (work, wait) required')
        work, waiting = row
        if type(work) is not int or not 1 <= work <= MAX_TIME:
            raise ValueError(f'stages[{i}].work: whole number 1 to 1000 required')
        if type(waiting) is not int or not 0 <= waiting <= MAX_TIME:
            raise ValueError(f'stages[{i}].wait: whole number 0 to 1000 required')
    if type(wait_limit) is not int or not 0 <= wait_limit <= 100:
        raise ValueError('wait_limit: whole number 0 to 100 required')
    work = sum(row[0] for row in stages)
    waiting = sum(row[1] for row in stages)
    total = work + waiting
    return {'flow_waste_validated': False, 'not_claimed': NOT_CLAIMED,
            'work_total': work, 'wait_total': waiting, 'elapsed_total': total,
            'wait_pct': waiting * 100 // total,
            'within_limit': waiting * 100 <= wait_limit * total,
            'waiting_positions': tuple(i for i in range(len(stages)) if stages[i][1] > 0)}
