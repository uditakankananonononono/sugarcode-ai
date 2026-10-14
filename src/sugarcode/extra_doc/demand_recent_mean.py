"""Row 454: Demand Forecasting - Predicts needs.

PARTIAL: returns the floored average and remainder of a supplied recent
window, plus the difference from the previous window when available.
This is arithmetic, not a validated prediction or statistical model.
Caps of 2-24 observations, integer counts 0-10000 and a window of
1 to the observation count are this module's own choices.
"""
MAX_OBSERVATIONS = 24
MAX_COUNT = 10000
NOT_CLAIMED = ('predictive_accuracy', 'statistical_model', 'seasonality')


def recent_mean(counts, window):
    if type(counts) is not tuple or not 2 <= len(counts) <= MAX_OBSERVATIONS:
        raise ValueError('counts: tuple of 2 to 24 observations required')
    for i,value in enumerate(counts):
        if type(value) is not int or not 0 <= value <= MAX_COUNT:
            raise ValueError(f'counts[{i}]: whole number 0 to 10000 required')
    if type(window) is not int or not 1 <= window <= len(counts):
        raise ValueError('window: whole number 1 to observation count required')
    total = sum(counts[-window:])
    mean, remainder = divmod(total, window)
    previous = None
    if len(counts) >= 2 * window:
        previous = sum(counts[-2 * window:-window]) // window
    return {'demand_recent_mean_validated': False, 'not_claimed': NOT_CLAIMED,
            'mean': mean, 'remainder': remainder, 'window_total': total,
            'previous_mean': previous,
            'change': None if previous is None else mean - previous}
