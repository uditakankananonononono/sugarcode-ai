"""Row 452: Supply Chain Design - Structures logistics.

PARTIAL: compares supplied sequential-stage capacities with a required
throughput. Reports the smallest capacity, its positions, and shortfall
positions. No network design, transport plan or real throughput model.
Caps of 2-12 stages and capacities/required throughput 1-10000 are this
module's own choices, not a domain standard.
"""
MAX_STAGES = 12
MAX_CAPACITY = 10000
NOT_CLAIMED = ('network_design', 'transport_plan', 'real_throughput')


def capacity(stages, required):
    if type(stages) is not tuple or not 2 <= len(stages) <= MAX_STAGES:
        raise ValueError('stages: tuple of 2 to 12 capacities required')
    for i, value in enumerate(stages):
        if type(value) is not int or not 1 <= value <= MAX_CAPACITY:
            raise ValueError(f'stages[{i}]: whole number 1 to 10000 required')
    if type(required) is not int or not 1 <= required <= MAX_CAPACITY:
        raise ValueError('required: whole number 1 to 10000 required')
    bottleneck = stages[min(range(len(stages)), key=lambda i: stages[i])]
    limiting = tuple(i for i in range(len(stages)) if stages[i] == bottleneck)
    shortfalls = tuple(i for i in range(len(stages)) if stages[i] < required)
    return {'chain_capacity_validated': False, 'not_claimed': NOT_CLAIMED,
            'bottleneck': bottleneck, 'limiting_positions': limiting,
            'shortfall_positions': shortfalls, 'all_sufficient': not shortfalls,
            'margin': bottleneck - required}
