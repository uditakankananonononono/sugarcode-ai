"""Row 631 Metrics Collection (PARTIAL): exact summary of one supplied list of latency-style samples.

summarize(samples, percentiles) takes 1..1000 whole samples (0..10**9) and 1..10 whole percentiles (1..100).
It returns count, minimum, maximum, sum, the mean as an exact reduced fraction, and for each percentile p the
nearest-rank value: the sorted sample at 1-based rank ceil(p * count / 100). These ranges are this module's own
choices, not spec values. It summarises the numbers it is given. It collects nothing, has no clock, units,
labels, scraping, storage or export, and says nothing about how fast any system is."""
from math import gcd

MAX_SAMPLES = 1000
MAX_VALUE = 10 ** 9
MAX_PERCENTILES = 10
NOT_CLAIMED = ("metric collection", "measurement accuracy", "units or timing", "storage or export",
               "performance of any system", "alerting thresholds")


def summarize(samples, percentiles):
    if type(samples) is not list or not 1 <= len(samples) <= MAX_SAMPLES:
        raise ValueError(f"samples: list of 1 to {MAX_SAMPLES} required")
    if type(percentiles) is not list or not 1 <= len(percentiles) <= MAX_PERCENTILES:
        raise ValueError(f"percentiles: list of 1 to {MAX_PERCENTILES} required")
    for i, v in enumerate(samples):
        if type(v) is not int or not 0 <= v <= MAX_VALUE:
            raise ValueError(f"samples[{i}]: whole number 0 to {MAX_VALUE} required")
    for i, p in enumerate(percentiles):
        if type(p) is not int or not 1 <= p <= 100:
            raise ValueError(f"percentiles[{i}]: whole number 1 to 100 required")
    ordered = sorted(samples)
    n, total = len(ordered), sum(ordered)
    g = gcd(total, n)
    return {"count": n, "minimum": ordered[0], "maximum": ordered[-1], "sum": total,
            "mean_numerator": total // g, "mean_denominator": n // g,
            "percentile_values": [ordered[-(-p * n // 100) - 1] for p in percentiles],
            "metrics_validated": False, "not_claimed": NOT_CLAIMED}
