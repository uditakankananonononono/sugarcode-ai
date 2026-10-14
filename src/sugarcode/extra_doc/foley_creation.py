"""Row 308 foley creation (PARTIAL): synthesises simple everyday sound effects as sample lists.

An impact is a sum of exponentially damped sines; a layered effect places impacts at time offsets and sums them.
Reports length, peak, the first sample index where the envelope falls below a threshold, and onset indices.
No claim that the result sounds like a real door, footstep or any object."""
import math

MAX_SAMPLES = 200000
SR_RANGE = (1000, 96000)
STATUS_NOTE = ("PARTIAL: damped-sine synthesis of simple impacts with computed length, peak and decay point; "
               "no claim of realism or of matching any real object")


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name}: number required")
    if abs(v) > 1e9:
        raise ValueError(f"{name}: magnitude above 1e9")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return float(v)


def impact(partials, decay_s, duration_s, sample_rate=8000):
    """partials: list of (freq_hz, amplitude). Sample n = sum a*exp(-n/(sr*decay))*sin(2 pi f n / sr)."""
    sr = _num(sample_rate, "sample_rate", *SR_RANGE)
    d = _num(decay_s, "decay_s", 0.001, 10)
    dur = _num(duration_s, "duration_s", 0.001, 10)
    count = int(round(dur * sr))
    if count > MAX_SAMPLES:
        raise ValueError(f"more than {MAX_SAMPLES} samples")
    if not isinstance(partials, (list, tuple)) or not 1 <= len(partials) <= 16:
        raise ValueError("partials: 1 to 16 required")
    ps = []
    for p in partials:
        if not isinstance(p, (list, tuple)) or len(p) != 2:
            raise ValueError("partial: (freq, amplitude) required")
        ps.append((_num(p[0], "freq", 1, sr / 2), _num(p[1], "amplitude", 0, 10)))
    return [sum(a * math.exp(-n / (sr * d)) * math.sin(2 * math.pi * f * n / sr) for f, a in ps)
            for n in range(count)]


def layer(events, sample_rate=8000):
    """events: list of (offset_s, samples). Returns summed buffer and onset indices."""
    sr = _num(sample_rate, "sample_rate", *SR_RANGE)
    if not isinstance(events, (list, tuple)) or not 1 <= len(events) <= 64:
        raise ValueError("events: 1 to 64 required")
    placed = []
    for e in events:
        if not isinstance(e, (list, tuple)) or len(e) != 2:
            raise ValueError("event: (offset_s, samples) required")
        off = _num(e[0], "offset_s", 0, 10)
        if not isinstance(e[1], (list, tuple)):
            raise ValueError("samples: list required")
        placed.append((int(round(off * sr)), e[1]))
    total = max(i + len(s) for i, s in placed)
    if total > MAX_SAMPLES:
        raise ValueError(f"more than {MAX_SAMPLES} samples")
    out = [0.0] * total
    for i, s in placed:
        for k, v in enumerate(s):
            out[i + k] += _num(v, "sample", -1e6, 1e6)
    return {"samples": out, "onsets": sorted(i for i, _ in placed), "length": total, "peak": max(abs(x) for x in out)}


def decay_point(samples, threshold):
    """First index after the peak where |x| stays below threshold*peak for the rest of the buffer; None if never."""
    th = _num(threshold, "threshold", 0.0001, 1)
    if not isinstance(samples, (list, tuple)) or not samples or len(samples) > MAX_SAMPLES:
        raise ValueError("samples: non-empty list within limit required")
    xs = [abs(_num(x, "sample", -1e6, 1e6)) for x in samples]
    peak = max(xs)
    if peak == 0:
        return None
    pk = xs.index(peak)
    limit = th * peak
    idx = None
    for i in range(len(xs) - 1, pk, -1):
        if xs[i] >= limit:
            break
        idx = i
    return idx
