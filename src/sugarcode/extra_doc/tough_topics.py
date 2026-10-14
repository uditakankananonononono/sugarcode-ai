"""Row 723 Difficult Conversations (PARTIAL): pack ordered topics into sessions under two caps.

topics is a tuple of 0..40 entries; each entry is a tuple (name, level) with name a str of 1..40 characters and
level a whole number 1..5. A topic with level 4 or 5 counts as tough (this module's own cutoff). per_session is
a whole number 1..10: the most tough topics allowed in one session. A session also holds at most 12 topics in
all. Topics stay in the given order and are packed greedily: a topic starts a new session when the current
session already holds 12 topics, or when the topic is tough and the current session already holds per_session
tough topics. The result lists each session's (position, name) pairs and the tough count per session. The
cutoff, caps and packing rule are this module's own choices. It is position bookkeeping only: it does not know
what any topic is, whether it is actually hard to discuss, or how to hold any conversation."""

MAX_TOPICS = 40
MAX_NAME = 40
MAX_LEVEL = 5
TOUGH_AT = 4
MAX_PER_SESSION = 10
MAX_SESSION = 12
NOT_CLAIMED = ("what any topic is", "whether a topic is actually difficult", "how to hold any conversation",
               "whether the packing order is kind or wise", "anyone's emotional state")


def plan(topics, per_session):
    if type(topics) is not tuple or len(topics) > MAX_TOPICS:
        raise ValueError(f"topics: tuple of 0 to {MAX_TOPICS} entries required")
    if type(per_session) is not int or not 1 <= per_session <= MAX_PER_SESSION:
        raise ValueError(f"per_session: whole number 1 to {MAX_PER_SESSION} required")
    for i, e in enumerate(topics):
        if type(e) is not tuple or len(e) != 2:
            raise ValueError(f"topics[{i}]: (name, level) tuple required")
        if type(e[0]) is not str or not 1 <= len(e[0]) <= MAX_NAME:
            raise ValueError(f"topics[{i}] name: str of 1 to {MAX_NAME} characters required")
        if type(e[1]) is not int or not 1 <= e[1] <= MAX_LEVEL:
            raise ValueError(f"topics[{i}] level: whole number 1 to {MAX_LEVEL} required")
    sessions, cur, tough = [], [], 0
    for i, (name, level) in enumerate(topics):
        hard = level >= TOUGH_AT
        if cur and (len(cur) >= MAX_SESSION or (hard and tough >= per_session)):
            sessions.append((tuple(cur), tough))
            cur, tough = [], 0
        cur.append((i, name))
        if hard:
            tough += 1
    if cur:
        sessions.append((tuple(cur), tough))
    return {"sessions": tuple(s for s, _ in sessions), "tough": tuple(t for _, t in sessions),
            "tough_topics_validated": False, "not_claimed": NOT_CLAIMED}
