"""Audio Engine - exact mixer for integer sample tracks with gains and 16-bit clipping.

Pure function over caller data. No audio files, no devices, no network, no clock, no
floats, no randomness. Input: tracks, 1..8 lists of 1..1000 int samples, each in
-32768..32767; gains, one [num, den] pair per track with num an int -100..100 and den an
int 1..100 (the gain is num/den).

Mix: the output has the length of the longest track; shorter tracks count as silence
(0) past their end. Each output sample is the exact sum over tracks of gain * sample,
rounded half up (floor(x + 1/2)) and then clipped into -32768..32767. The result gives
the mixed samples, the number of clipped samples (those that changed by clipping), the
peak absolute value after clipping, the energy (sum of squares after clipping) and the
mean power (energy / length) as an exact Fraction string.

Scope: PARTIAL for the Audio Engine line. Exact integer mixing of already-sampled data.
It is not an audio engine in the general sense: no resampling, no filters, no effects,
no file formats, no playback, no real-time processing.

Not claimed: that the output sounds good, that the gains are right for any purpose, that
the samples are real recorded audio, or anything about the real world. Every claim flag
in the result is False.
"""
from fractions import Fraction

MAX_TRACKS = 8
MAX_SAMPLES = 1000
SAMPLE_MIN = -32768
SAMPLE_MAX = 32767
_TOP = frozenset({"tracks", "gains"})

NOT_CLAIMED = (
    "the output sounds good",
    "the gains are right for any purpose",
    "the samples are real recorded audio",
    "real-world outcome",
)
CLAIMS = {"sounds_good": False, "gains_suitable": False, "real_audio": False, "real_world": False}


class AudioError(ValueError):
    pass


def _int(v, lo, hi, name):
    if type(v) is not int:
        raise AudioError(f"{name} must be an int")
    if v < lo or v > hi:
        raise AudioError(f"{name} out of range")
    return v


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise AudioError("data keys must be exactly gains, tracks")
    tr = data["tracks"]
    if not isinstance(tr, list) or not 1 <= len(tr) <= MAX_TRACKS:
        raise AudioError("tracks must be a list of 1..8 tracks")
    gn = data["gains"]
    if not isinstance(gn, list) or len(gn) != len(tr):
        raise AudioError("gains must be a list with one [num, den] pair per track")
    tracks = []
    for t in tr:
        if not isinstance(t, list) or not 1 <= len(t) <= MAX_SAMPLES:
            raise AudioError("each track must be a list of 1..1000 samples")
        tracks.append([_int(s, SAMPLE_MIN, SAMPLE_MAX, "sample") for s in t])
    gains = []
    for g in gn:
        if not isinstance(g, list) or len(g) != 2:
            raise AudioError("gains must be a list with one [num, den] pair per track")
        gains.append(Fraction(_int(g[0], -100, 100, "gain numerator"), _int(g[1], 1, 100, "gain denominator")))
    return tracks, gains


def audio_engine(data):
    tracks, gains = _validate(data)
    n = max(len(t) for t in tracks)
    out = []
    clipped = 0
    for i in range(n):
        x = sum(g * (t[i] if i < len(t) else 0) for t, g in zip(tracks, gains))
        r = (x + Fraction(1, 2)).__floor__()
        c = min(SAMPLE_MAX, max(SAMPLE_MIN, r))
        if c != r:
            clipped += 1
        out.append(c)
    energy = sum(s * s for s in out)
    return {
        "status": "completed",
        "samples": out,
        "length": n,
        "clipped": clipped,
        "peak": max(abs(s) for s in out),
        "energy": energy,
        "mean_power": str(Fraction(energy, n)),
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
