"""Row 1188: Epidemic Response.

PARTIAL: compares supplied abstract stock with cumulative supplied demands.
Caps are module-local choices, not epidemiological units or standards.
No outbreak planning, safety assessment or medical decisions.
"""
NOT_CLAIMED = ('outbreak_planning', 'safety_assessment', 'medical_decisions')


def margins(demands, stock):
    if type(demands) is not tuple or not 1 <= len(demands) <= 20:
        raise ValueError('demands: tuple of 1 to 20 counts required')
    for i,value in enumerate(demands):
        if type(value) is not int or not 0 <= value <= 1000:
            raise ValueError(f'demands[{i}]: whole number 0 to 1000 required')
    if type(stock) is not int or not 0 <= stock <= 20000:
        raise ValueError('stock: whole number 0 to 20000 required')
    remaining = tuple(stock-sum(demands[:i+1]) for i in range(len(demands)))
    return {'abstract_resource_margin_validated': False, 'not_claimed': NOT_CLAIMED,
            'remaining': remaining, 'shortfall_positions': tuple(i for i in range(len(remaining)) if remaining[i] < 0),
            'total_demand': sum(demands)}
