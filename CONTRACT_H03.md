# H03 slug-rule characterization (TEST ONLY, AUTHORED, NOT RUN)

Base/parent: exactly 8d5081d942eca77fd61957596172b4f1f497f0c5 (H02 landed). Adds two files, edits none; no behavior change, no unification.
Authority: peer GO relayed by Main 2:07:32 PM IST (not authority by itself).

Files: tests/self_improve/test_h03_slug_rule_characterization.py (A), CONTRACT_H03.md (A).

Pins (source read at 8d5081d9, nothing run):
- events.GapEventStore._path (events.py 65-69): keeps chars with isalnum() or in "-_"; refuses (plain ValueError "unsafe module slug") if the filtered text differs from the slug or is empty.
- proposal_preflight_r01._identity (53-57): `_text` requires an exact str (ProposalPreflightError, a ValueError subclass); then removes "-" and "_" and requires isalnum().
Characterized divergences: punctuation-only slugs ("-", "--", "---", "_", "__", "-_", "_-_-") accepted by events, refused by preflight; str subclasses accepted by events, refused by preflight;
non-str: events TypeError (None, int), preflight typed refusal; exception CLASSES differ though both are ValueErrors. Both refuse "", spaces, "../x", ".", "/", "\\", newline, U+2028, NUL, astral emoji; both accept Unicode letters/digits and "-"/"_" mixed with alphanumerics.
Also pins that GapEvent.__post_init__ does not check slug shape (it only checks exact str type), and the public append refuses "../escape" and writes "---.gap-events.jsonl".
Header comment in the test file: "characterization, do not unify".

Unverified / NOT RUN: pytest, import, compile. Case outcomes (including "²" and "٣" counting as isalnum, and the append writing a file named "---.gap-events.jsonl") are reasoned from the two functions, not executed.
