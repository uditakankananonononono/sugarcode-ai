"""Row 663 Observer Pattern (PARTIAL): which observers are told about each event, and in what order.

subscriptions is a list of 1..32 (name, topic, priority) tuples: name and topic are 1..30 characters of a-z,
0-9 and underscore starting with a letter (ASCII only), priority a whole number -100..100. Names are distinct.
events is a list of 1..50 topic names. An event goes to every subscription with that topic, highest priority
first, equal priorities in subscription order. The result lists (event_index, name) deliveries in event order
and the indexes of events nobody observes. These ranges are this module's own choices. It only orders
supplied data. It registers no callbacks, runs no code and says nothing about thread safety or delivery."""
import re

MAX_SUBS, MAX_EVENTS = 32, 50
NOT_CLAIMED = ("an implementation of the pattern", "callback execution", "thread safety",
               "delivery guarantees", "design quality")
_NAME = re.compile(r"[a-z][a-z0-9_]{0,29}")


def _name(label, v):
    if type(v) is not str or _NAME.fullmatch(v) is None:
        raise ValueError(f"{label}: name of a-z, 0-9, _ (1 to 30, starting with a letter) required")
    return v


def notify(subscriptions, events):
    if type(subscriptions) is not list or not 1 <= len(subscriptions) <= MAX_SUBS:
        raise ValueError(f"subscriptions: list of 1 to {MAX_SUBS} required")
    for i, sub in enumerate(subscriptions):
        if type(sub) is not tuple or len(sub) != 3:
            raise ValueError(f"subscriptions[{i}]: (name, topic, priority) tuple required")
        _name(f"subscriptions[{i}] name", sub[0])
        _name(f"subscriptions[{i}] topic", sub[1])
        if type(sub[2]) is not int or not -100 <= sub[2] <= 100:
            raise ValueError(f"subscriptions[{i}] priority: whole number -100 to 100 required")
    if len({s[0] for s in subscriptions}) != len(subscriptions):
        raise ValueError("subscriptions: names must be distinct")
    if type(events) is not list or not 1 <= len(events) <= MAX_EVENTS:
        raise ValueError(f"events: list of 1 to {MAX_EVENTS} required")
    for i, e in enumerate(events):
        _name(f"events[{i}]", e)
    deliveries, unobserved = [], []
    for i, topic in enumerate(events):
        hits = sorted((k for k, s in enumerate(subscriptions) if s[1] == topic),
                      key=lambda k: (-subscriptions[k][2], k))
        deliveries.extend((i, subscriptions[k][0]) for k in hits)
        if not hits:
            unobserved.append(i)
    return {"deliveries": deliveries, "unobserved_events": unobserved,
            "observer_validated": False, "not_claimed": NOT_CLAIMED}
