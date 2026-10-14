"""Row 335 Game Design: exact core-loop composer over caller-supplied design pools.

The caller supplies pools of goals, actions, challenges and rewards (each item has an
id, a short text, a complexity cost, a fun weight and tags). compose() enumerates every
one-of-each combination, keeps those whose total complexity fits the budget and whose
tags are compatible (the challenge shares a tag with the action, the reward shares a tag
with the goal), and returns the combination with the largest total fun weight (ties go
to the lowest tuple of ids). The output includes a generated design brief and the loop.

NOT_CLAIMED: that the design is fun, balanced, original or accessible; playtesting;
market fit; any measured player experience. The fun weights are numbers the caller
supplied, not measurements. Human review is required before use.
"""
import itertools
import unicodedata

MAX_POOL = 5
MAX_TAGS = 4
MAX_ID = 30
MAX_TEXT = 80
MAX_COMPLEXITY_ITEM = 10
MAX_FUN = 100
MAX_BUDGET = 40
POOLS = ("goals", "actions", "challenges", "rewards")
_FIELDS = {"id", "text", "complexity", "fun", "tags"}


def _text(value, name, limit):
    if type(value) is not str or not 1 <= len(value) <= limit:
        raise ValueError(f"{name}: text of 1..{limit} characters required")
    if value != value.strip() or any(unicodedata.category(ch).startswith("C") for ch in value):
        raise ValueError(f"{name}: trimmed visible text required")
    return value


def _int(value, name, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError(f"{name}: integer in [{lo}, {hi}] required")
    return value


def _pool(value, name):
    if type(value) is not list or not 1 <= len(value) <= MAX_POOL:
        raise ValueError(f"{name}: list of 1..{MAX_POOL} items required")
    items, seen = [], set()
    for i, raw in enumerate(value):
        label = f"{name}[{i}]"
        if type(raw) is not dict or set(raw) != _FIELDS:
            raise ValueError(f"{label}: exact keys id, text, complexity, fun, tags required")
        ident = _text(raw["id"], f"{label}.id", MAX_ID)
        if ident in seen:
            raise ValueError(f"{label}: duplicate id")
        seen.add(ident)
        tags = raw["tags"]
        if type(tags) is not list or not 1 <= len(tags) <= MAX_TAGS:
            raise ValueError(f"{label}.tags: list of 1..{MAX_TAGS} tags required")
        tag_set = {_text(t, f"{label}.tags", MAX_ID) for t in tags}
        if len(tag_set) != len(tags):
            raise ValueError(f"{label}.tags: duplicate tag")
        items.append({
            "id": ident,
            "text": _text(raw["text"], f"{label}.text", MAX_TEXT),
            "complexity": _int(raw["complexity"], f"{label}.complexity", 0, MAX_COMPLEXITY_ITEM),
            "fun": _int(raw["fun"], f"{label}.fun", 0, MAX_FUN),
            "tags": tag_set,
        })
    return items


def compose(goals, actions, challenges, rewards, max_complexity):
    pools = [_pool(v, n) for v, n in zip((goals, actions, challenges, rewards), POOLS)]
    budget = _int(max_complexity, "max_complexity", 0, MAX_BUDGET)
    best, count = None, 0
    for goal, action, challenge, reward in itertools.product(*pools):
        if goal["complexity"] + action["complexity"] + challenge["complexity"] + reward["complexity"] > budget:
            continue
        if not action["tags"] & challenge["tags"] or not goal["tags"] & reward["tags"]:
            continue
        count += 1
        fun = goal["fun"] + action["fun"] + challenge["fun"] + reward["fun"]
        key = (-fun, goal["id"], action["id"], challenge["id"], reward["id"])
        if best is None or key < best[0]:
            best = (key, goal, action, challenge, reward)
    if best is None:
        return {"status": "no_compatible_design", "feasible_count": 0, "design": None,
                "brief": "", "loop": [], "playtest_verified": False, "external_effects": []}
    _, goal, action, challenge, reward = best
    return {
        "status": "designed",
        "feasible_count": count,
        "design": {"goal": goal["id"], "action": action["id"], "challenge": challenge["id"],
                   "reward": reward["id"], "total_fun_weight": -best[0][0],
                   "total_complexity": sum(x["complexity"] for x in best[1:])},
        "brief": f"Goal: {goal['text']} Players act by {action['text']} Challenge: {challenge['text']} "
                 f"Reward: {reward['text']}",
        "loop": [f"goal: {goal['text']}", f"act: {action['text']}",
                 f"challenge: {challenge['text']}", f"reward: {reward['text']}"],
        "playtest_verified": False,
        "review_required": True,
        "external_effects": [],
    }
