"""Row 1169: Wound Care.

PARTIAL: multiplies supplied abstract rectangular dimensions and reports
areas, their total, and positions exceeding a supplied area threshold.
No wound measurement, care planning or clinical interpretation.
Caps of 1-20 pairs, dimensions 1-100 and threshold 0-10000 are this
module's own choices, not clinical units or standards.
"""
MAX_ROWS = 20
LIMIT = 100
MAX_AREA = 10000
NOT_CLAIMED = ('wound_measurement', 'care_planning', 'clinical_interpretation')


def areas(rectangles, threshold):
    if type(rectangles) is not tuple or not 1 <= len(rectangles) <= MAX_ROWS:
        raise ValueError('rectangles: tuple of 1 to 20 pairs required')
    for i,row in enumerate(rectangles):
        if type(row) is not tuple or len(row) != 2:
            raise ValueError(f'rectangles[{i}]: pair (width, height) required')
        for name,value in zip(('width','height'),row):
            if type(value) is not int or not 1 <= value <= LIMIT:
                raise ValueError(f'rectangles[{i}].{name}: whole number 1 to 100 required')
    if type(threshold) is not int or not 0 <= threshold <= MAX_AREA:
        raise ValueError('threshold: whole number 0 to 10000 required')
    values = tuple(width * height for width,height in rectangles)
    above = tuple(i for i in range(len(values)) if values[i] > threshold)
    return {'abstract_rectangle_area_validated': False, 'not_claimed': NOT_CLAIMED,
            'areas': values, 'total_area': sum(values), 'above_positions': above,
            'above_count': len(above)}
