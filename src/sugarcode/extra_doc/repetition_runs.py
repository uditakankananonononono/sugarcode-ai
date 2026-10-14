"""Row 471: Robotic Process Automation - Automates repetitive tasks.

PARTIAL: identifies consecutive repeated supplied task indices, returning
run starts, lengths and repeated-run starts. No robotic execution,
automation suitability or external effects. Caps of 1-30 tasks and
indices 0-100 are this module's own choices, not a domain standard.
"""
MAX_TASKS = 30
MAX_INDEX = 100
NOT_CLAIMED = ('robotic_execution', 'automation_suitability', 'external_effects')


def runs(tasks):
    if type(tasks) is not tuple or not 1 <= len(tasks) <= MAX_TASKS:
        raise ValueError('tasks: tuple of 1 to 30 indices required')
    for i,value in enumerate(tasks):
        if type(value) is not int or not 0 <= value <= MAX_INDEX:
            raise ValueError(f'tasks[{i}]: whole number 0 to 100 required')
    starts = (0,) + tuple(i for i in range(1,len(tasks)) if tasks[i] != tasks[i-1])
    ends = starts[1:] + (len(tasks),)
    lengths = tuple(end-start for start,end in zip(starts,ends))
    repeated = tuple(starts[i] for i in range(len(starts)) if lengths[i] > 1)
    return {'repetition_runs_validated': False, 'not_claimed': NOT_CLAIMED,
            'starts': starts, 'lengths': lengths, 'repeated_starts': repeated,
            'saved_if_collapsed': len(tasks) - len(starts)}
