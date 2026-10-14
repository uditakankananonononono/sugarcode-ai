"""Row 307 mastering (PARTIAL): measures a mono PCM buffer against distribution targets and computes the gain.

Reports sample peak and RMS in dBFS, DC offset, clipped-sample count, crest factor and the gain that moves RMS to a
target without the peak passing a ceiling. Sample-peak only (no true-peak, no LUFS, no K-weighting). No claim of
audio quality, taste or platform acceptance."""
import math

MAX_SAMPLES = 1000000
MAX_ABS_DB = 200
STATUS_NOTE = ("PARTIAL: sample-peak and plain RMS measurement with a gain calculation; no true-peak, no LUFS, "
               "no claim of audio quality or platform acceptance")


def _db(v):
    return 20 * math.log10(v)


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


def master(samples, target_rms_db=-16.0, ceiling_db=-1.0):
    if not isinstance(samples, (list, tuple)):
        raise ValueError("samples: list required")
    if len(samples) > MAX_SAMPLES:
        raise ValueError(f"samples: more than {MAX_SAMPLES}")
    if not samples:
        raise ValueError("samples: at least one required")
    t = _num(target_rms_db, "target_rms_db", -MAX_ABS_DB, 0)
    c = _num(ceiling_db, "ceiling_db", -MAX_ABS_DB, 0)
    xs = [_num(s, "sample", -1e6, 1e6) for s in samples]
    n = len(xs)
    peak = max(abs(x) for x in xs)
    dc = sum(xs) / n
    clipped = sum(1 for x in xs if abs(x) >= 1.0)
    if peak == 0:
        return {"samples": n, "peak_db": -math.inf, "rms_db": -math.inf, "dc_offset": 0.0, "clipped": 0,
                "crest_db": None, "gain_db": 0.0, "limited_by": "silence", "meets_ceiling": True,
                "status": STATUS_NOTE}
    rms = peak * math.sqrt(math.fsum((x / peak) ** 2 for x in xs) / n)
    want = t - _db(rms)
    room = c - _db(peak)
    gain = min(want, room)
    return {"samples": n, "peak_db": _db(peak), "rms_db": _db(rms), "dc_offset": dc + 0.0, "clipped": clipped,
            "crest_db": _db(peak) - _db(rms), "gain_db": gain,
            "limited_by": "ceiling" if room < want else "target",
            "meets_ceiling": _db(peak) + gain <= c + 1e-9, "status": STATUS_NOTE}


def apply_gain(samples, gain_db):
    g = _num(gain_db, "gain_db", -MAX_ABS_DB, MAX_ABS_DB)
    if not isinstance(samples, (list, tuple)) or len(samples) > MAX_SAMPLES:
        raise ValueError("samples: list within limit required")
    k = 10 ** (g / 20)
    return [_num(s, "sample", -1e6, 1e6) * k for s in samples]
