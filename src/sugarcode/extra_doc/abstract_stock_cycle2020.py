"""Row 2020: Autopoiesis.

PARTIAL: supplied abstract integer stock plus production minus loss at
successive steps, with deficit positions. Local caps, no living-system,
self-production, organizational closure or sustainability validity.
"""
NOT_CLAIMED = ('living_system', 'self_production', 'organizational_closure', 'sustainability')


def cycle(initial, rows):
    if type(initial) is not int or not 0 <= initial <= 100:
        raise ValueError('initial: integer 0 to 100 required')
    if type(rows) is not tuple or not 1 <= len(rows) <= 20:
        raise ValueError('rows: tuple of 1 to 20 production-loss pairs required')
    for i,row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'rows[{i}]: pair (production, loss) required')
        for j,value in enumerate(row):
            if type(value) is not int or not 0 <= value <= 100:
                raise ValueError(f'rows[{i}][{j}]: integer 0 to 100 required')
    stocks = [initial]
    for production,loss in rows:
        stocks.append(stocks[-1]+production-loss)
    deficits = tuple(i for i in range(1,len(stocks)) if stocks[i] < 0)
    return {'abstract_stock_cycle_validated': False, 'not_claimed': NOT_CLAIMED,
            'stocks': tuple(stocks), 'deficit_steps': deficits, 'net_change': stocks[-1]-initial}
