"""Row 470: Workflow Automation - Eliminates manual steps.

PARTIAL: compares supplied before/after step durations, returning total
savings and improved/regressed positions. No actual automation, workflow
integration or feasibility claim. Caps of 1-20 pairs and integer durations
0-1000 are this module's own choices, not a domain standard.
"""
MAX_STEPS = 20
MAX_DURATION = 1000
NOT_CLAIMED = ('actual_automation', 'workflow_integration', 'feasibility')


def savings(steps):
    if type(steps) is not tuple or not 1 <= len(steps) <= MAX_STEPS:
        raise ValueError('steps: tuple of 1 to 20 pairs required')
    for i,row in enumerate(steps):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'steps[{i}]: pair (before, after) required')
        for name,value in zip(('before','after'),row):
            if type(value) is not int or not 0 <= value <= MAX_DURATION:
                raise ValueError(f'steps[{i}].{name}: whole number 0 to 1000 required')
    before = sum(row[0] for row in steps)
    after = sum(row[1] for row in steps)
    return {'workflow_savings_validated': False, 'not_claimed': NOT_CLAIMED,
            'before_total': before, 'after_total': after, 'saved': before - after,
            'improved_positions': tuple(i for i in range(len(steps)) if steps[i][1] < steps[i][0]),
            'regressed_positions': tuple(i for i in range(len(steps)) if steps[i][1] > steps[i][0])}
