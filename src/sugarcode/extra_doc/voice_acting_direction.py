"""Row 309 voice acting direction (PARTIAL): pacing notes for recorded lines.

For each line (text, seconds, target words per minute) computes words per minute, the ratio to target and a
direction note: slower, faster or on pace (tolerance 10 percent). Also pause gaps between consecutive takes.
Pacing only: no judgment of emotion, delivery, accent or acting quality."""
import math

MAX_LINES = 500
TOLERANCE = 0.10
STATUS_NOTE = ("PARTIAL: words-per-minute pacing against a target with a direction note; "
               "no judgment of emotion, delivery or acting quality")


def _num(v, name, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name}: number required")
    if abs(v) > 1e9:
        raise ValueError(f"{name}: magnitude above 1e9")
    if isinstance(v, float) and not math.isfinite(v):
        raise ValueError(f"{name}: finite number required")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be within [{lo}, {hi}]")
    return v


def direct(lines):
    if not isinstance(lines, (list, tuple)) or not 1 <= len(lines) <= MAX_LINES:
        raise ValueError(f"lines: 1 to {MAX_LINES} required")
    out = []
    for ln in lines:
        if not isinstance(ln, dict) or not isinstance(ln.get("text"), str):
            raise ValueError("line: dict with text required")
        words = len(ln["text"].split())
        if words == 0:
            raise ValueError("line: text has no words")
        sec = _num(ln.get("seconds"), "seconds", 0.1, 3600)
        tgt = _num(ln.get("target_wpm", 150), "target_wpm", 30, 400)
        wpm = words * 60 / sec
        ratio = wpm / tgt
        note = "faster" if ratio > 1 + TOLERANCE else "slower" if ratio < 1 - TOLERANCE else "on pace"
        # note describes what the actor did; advice is the opposite
        advice = {"faster": "slow down", "slower": "speed up", "on pace": "hold pace"}[note]
        out.append({"words": words, "wpm": wpm, "ratio": ratio, "delivery": note, "advice": advice})
    return {"lines": out, "slow_down": sum(1 for r in out if r["advice"] == "slow down"),
            "speed_up": sum(1 for r in out if r["advice"] == "speed up"), "status": STATUS_NOTE}
