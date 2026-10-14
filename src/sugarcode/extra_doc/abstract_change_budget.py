"""Row 1194: Lifestyle Modification.

PARTIAL: sums absolute differences between paired supplied abstract integer
values and compares that change cost to a supplied budget. Caps are local
choices, not clinical units or standards. No lifestyle effectiveness,
health outcome assessment or medical advice.
"""
NOT_CLAIMED = ('lifestyle_effectiveness', 'health_outcome_assessment', 'medical_advice')


def changes(rows, budget):
    if type(rows) is not tuple or not 1 <= len(rows) <= 20:
        raise ValueError('rows: tuple of 1 to 20 value pairs required')
    for i,row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'rows[{i}]: pair (before, after) required')
        for j,value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 1000:
                raise ValueError(f'rows[{i}][{j}]: whole number 0 to 1000 required')
    if type(budget) is not int or not 0 <= budget <= 20000:
        raise ValueError('budget: whole number 0 to 20000 required')
    costs = tuple(abs(after-before) for before,after in rows)
    total = sum(costs)
    return {'abstract_change_budget_validated': False, 'not_claimed': NOT_CLAIMED,
            'change_costs': costs, 'total_cost': total, 'within_budget': total <= budget,
            'remaining_budget': budget-total}
