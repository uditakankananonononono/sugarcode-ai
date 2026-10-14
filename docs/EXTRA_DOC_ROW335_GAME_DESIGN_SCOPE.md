# Row335 Game Design

Exact description: "Creates interactive entertainment".

Native standalone module src/sugarcode/extra_doc/game_design335.py. New files only; no
extra_doc/__init__.py is needed. Core-loop composer: from caller-supplied pools of goals,
actions, challenges and rewards it enumerates every one-of-each combination, keeps those within a
complexity budget whose tags are compatible (challenge shares a tag with the action, reward shares
a tag with the goal), and returns the maximum total fun weight (ties: lowest ids). It also
generates a design brief and the four-step loop. Fun weights are caller numbers.

Caps: 1..5 items per pool, id 1..30 and text 1..80 trimmed visible characters, 1..4 unique tags
per item, complexity 0..10 and fun 0..100 as strict ints (bool and float refused), budget 0..40,
exact item keys, unique ids per pool; all checks run before enumeration (at most 625 combinations).

SCOPED exact supplied-pool core-loop composition, literal PARTIAL.
NOT_CLAIMED fun, balance, originality, accessibility, playtesting, market fit, engine
implementation, publication. No external effects. Human design review required.
Independent audit required.
