"""Row 722 Boundary Setting : accept requests in order while a fixed budget lasts, refuse the rest.

budget is a whole number 0..10000. requests is a tuple of 0..50 whole numbers, each 1..10000 (the cost of a
request). Requests are taken in the given order: a request is accepted when its cost is at most what remains,
and the remaining budget drops by that cost. A refused request does not stop later, cheaper ones from being
accepted. The result lists the accepted and refused request positions and the remainder. Ranges are this
module's own choices. It is integer bookkeeping only: it does not know what any request is, whether refusing
it is right or kind, or whether any resource is protected."""

MAX_BUDGET = 10000
MAX_REQUESTS = 50
NOT_CLAIMED = ("what a request is", "whether a refusal is appropriate", "protection of any resource",
               "how a refusal is communicated", "fairness of the order")


def gate(budget, requests):
    if type(budget) is not int or not 0 <= budget <= MAX_BUDGET:
        raise ValueError(f"budget: whole number 0 to {MAX_BUDGET} required")
    if type(requests) is not tuple or len(requests) > MAX_REQUESTS:
        raise ValueError(f"requests: tuple of 0 to {MAX_REQUESTS} whole numbers required")
    for i, c in enumerate(requests):
        if type(c) is not int or not 1 <= c <= MAX_BUDGET:
            raise ValueError(f"requests[{i}]: whole number 1 to {MAX_BUDGET} required")
    left = budget
    accepted, refused = [], []
    for i, c in enumerate(requests):
        if c <= left:
            left -= c
            accepted.append(i)
        else:
            refused.append(i)
    return {"accepted": tuple(accepted), "refused": tuple(refused), "remaining": left,
            "limit_gate_validated": False, "not_claimed": NOT_CLAIMED}
