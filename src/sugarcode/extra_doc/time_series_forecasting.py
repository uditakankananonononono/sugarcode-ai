"""Row 553 time series forecasting: Holt linear-trend exponential smoothing in exact Fractions.

history is a list of 3 to 200 whole numbers from -1e9 to 1e9, oldest first. alpha_bps and beta_bps are the level
and trend smoothing weights in basis points (1 to 10000, so 5000 means 1/2). The level starts at history[0] and the
trend at history[1] - history[0]. For each later value y the one-step prediction is level + trend, its error is
y - prediction, then level = alpha * y + (1 - alpha) * (level + trend) and
trend = beta * (new level - old level) + (1 - beta) * trend. horizon (1 to 24) periods are forecast as
level + h * trend for h = 1 .. horizon from the final level and trend. mae is the mean absolute one-step error over
the history[1:] values. A straight-line history is continued exactly. A fit to past values is not a promise about
the future, and the method models neither seasonality nor turning points."""
from fractions import Fraction

MAX_HISTORY = 200
MAX_ABS = 10**9
MAX_BPS = 10000
MAX_HORIZON = 24
STATUS_NOTE = ("PARTIAL: linear-trend smoothing of the supplied past only; no seasonality or turning points and "
               "no promise about the future")


def _int(v, name, lo, hi):
    if type(v) is not int:
        raise ValueError(f"{name}: integer required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within {lo} to {hi}")
    return v


def forecast(history, alpha_bps, beta_bps, horizon):
    alpha_bps = _int(alpha_bps, "alpha_bps", 1, MAX_BPS)
    beta_bps = _int(beta_bps, "beta_bps", 1, MAX_BPS)
    horizon = _int(horizon, "horizon", 1, MAX_HORIZON)
    if type(history) not in (list, tuple):
        raise ValueError("history: list required")
    if not 3 <= len(history) <= MAX_HISTORY:
        raise ValueError(f"history: 3 to {MAX_HISTORY} entries required")
    for i, v in enumerate(history):
        _int(v, f"history[{i}]", -MAX_ABS, MAX_ABS)
    alpha = Fraction(alpha_bps, MAX_BPS)
    beta = Fraction(beta_bps, MAX_BPS)
    level = Fraction(history[0])
    trend = Fraction(history[1] - history[0])
    abs_err = Fraction(0)
    for y in history[1:]:
        pred = level + trend
        abs_err += abs(y - pred)
        new_level = alpha * y + (1 - alpha) * pred
        trend = beta * (new_level - level) + (1 - beta) * trend
        level = new_level
    return {"level": level, "trend": trend,
            "forecast": [level + h * trend for h in range(1, horizon + 1)],
            "mae": abs_err / (len(history) - 1), "status_note": STATUS_NOTE}
