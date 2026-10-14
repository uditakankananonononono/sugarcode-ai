"""Row 945: Morphological Computation - Body as computation.

PARTIAL: computes supplied abstract integer force times displacement per
pair and total signed work. Caps are module-local choices without physical
units. No embodied computation, physical work accuracy or robotics claims.
"""
NOT_CLAIMED = ('embodied_computation', 'physical_work_accuracy', 'robotics_validity')


def work(rows):
    if type(rows) is not tuple or not 1 <= len(rows) <= 20:
        raise ValueError('rows: tuple of 1 to 20 integer pairs required')
    for i,row in enumerate(rows):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'rows[{i}]: pair (force, displacement) required')
        for j,value in enumerate(row):
            if type(value) is not int or not -100 <= value <= 100:
                raise ValueError(f'rows[{i}][{j}]: whole number -100 to 100 required')
    signed = tuple(force*distance for force,distance in rows)
    return {'abstract_body_work_validated': False, 'not_claimed': NOT_CLAIMED,
            'signed_work': signed, 'total_work': sum(signed),
            'negative_positions': tuple(i for i in range(len(signed)) if signed[i] < 0)}
