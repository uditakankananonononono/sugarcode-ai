"""Row 310 podcast production: episode timeline arithmetic.

From ordered segments (title, speaker, seconds) computes start offsets, chapter timestamps (H:MM:SS), total
length and per-speaker talk share as exact fractions. No claim of content quality, audio quality or audience fit."""
from fractions import Fraction
import math

MAX_SEGMENTS = 500
STATUS_NOTE = ("PARTIAL: timeline, chapter-timestamp and talk-share arithmetic over supplied segments; "
               "no claim of content or audio quality")


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name}: whole number required")
    if abs(v) > 1e9:
        raise ValueError(f"{name}: magnitude above 1e9")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return v


def stamp(sec):
    s = _num(sec, "seconds", 0, 359999)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


def produce(segments):
    if not isinstance(segments, (list, tuple)) or not 1 <= len(segments) <= MAX_SEGMENTS:
        raise ValueError(f"segments: 1 to {MAX_SEGMENTS} required")
    t = 0
    chapters = []
    talk = {}
    for sg in segments:
        if not isinstance(sg, dict) or not isinstance(sg.get("title"), str) or not sg["title"].strip():
            raise ValueError("segment: title required")
        spk = sg.get("speaker")
        if not isinstance(spk, str) or not spk.strip():
            raise ValueError("segment: speaker required")
        d = _num(sg.get("seconds"), "seconds", 1, 86400)
        chapters.append({"title": sg["title"], "start": t, "stamp": stamp(t), "seconds": d})
        talk[spk] = talk.get(spk, 0) + d
        t += d
    if t > 359999:
        raise ValueError("total length above 99:59:59")
    share = {k: Fraction(v, t) for k, v in sorted(talk.items())}
    return {"chapters": chapters, "total": t, "total_stamp": stamp(t), "talk_share": share,
            "dominant": max(sorted(talk), key=lambda k: talk[k]), "status": STATUS_NOTE}
