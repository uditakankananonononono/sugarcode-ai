"""Row 453: Inventory Management - Optimizes stock.

PARTIAL: computes stock position as on-hand plus incoming minus reserved,
and a top-up to a supplied target only when position is below a supplied
reorder point. No optimal inventory policy, lead times or demand model.
Caps of 0-10000 units for each input are this module's own choices,
not a domain standard. Target must be at least the reorder point.
"""
MAX_UNITS = 10000
NOT_CLAIMED = ('optimal_policy', 'lead_times', 'demand_model')


def position(on_hand, incoming, reserved, reorder_point, target):
    for name, value in (('on_hand', on_hand), ('incoming', incoming),
                        ('reserved', reserved), ('reorder_point', reorder_point),
                        ('target', target)):
        if type(value) is not int or not 0 <= value <= MAX_UNITS:
            raise ValueError(f'{name}: whole number 0 to 10000 required')
    if target < reorder_point:
        raise ValueError('target must be at least reorder_point')
    available = on_hand + incoming - reserved
    reorder = available < reorder_point
    top_up = target - available if reorder else 0
    return {'inventory_position_validated': False, 'not_claimed': NOT_CLAIMED,
            'position': available, 'reorder': reorder, 'top_up': top_up,
            'backlog': -available if available < 0 else 0}
