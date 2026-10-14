"""Cryptographic Protocol - exact toy Diffie-Hellman exchange over a small prime, with brute force.

Pure function over caller data. No network, no clock, no floats, no randomness. Input: p, a prime int
5..10007; g, an int 2..p-2; a and b, ints 1..p-2 (the two secrets). The data keys are exactly a, b, g,
p. p is checked prime by trial division.

Each side publishes g**secret mod p: A for a and B for b. Each side then raises the other's public
value to its own secret: shared_a = B**a mod p, shared_b = A**b mod p. The result gives "public_a",
"public_b", "shared_a", "shared_b", "agree" (the two are equal), and a brute-force check on this
tiny modulus: "recovered_exponent" (the smallest x in 1..p-1 with g**x mod p equal to A, or None),
"recovered_shared" (B**x mod p, or None) and "attack_matches" (it equals shared_a).

Scope: bounded for the Cryptographic Protocol line. A toy modulus that brute force breaks on purpose.
No real key size, no authentication, no randomness, no network, no real secrecy.

Not claimed: that this secures communication, that any value is a safe key or parameter, that the
exchange resists an active attacker, or anything about the real world. Every claim flag in the result
is False.
"""
NOT_CLAIMED = (
    "this secures communication",
    "any value is a safe key or parameter",
    "the exchange resists an active attacker",
    "real-world outcome",
)
CLAIMS = {"secure": False, "safe_parameters": False, "active_attacker": False, "real_world": False}


class ProtocolError(ValueError):
    pass


def _prime(n):
    if n < 2:
        return False
    d = 2
    while d * d <= n:
        if n % d == 0:
            return False
        d += 1
    return True


def _validate(data):
    if type(data) is not dict or set(data) != {"a", "b", "g", "p"}:
        raise ProtocolError("data keys must be exactly a, b, g, p")
    p = data["p"]
    if type(p) is not int:
        raise ProtocolError("p must be an int")
    if not 5 <= p <= 10007:
        raise ProtocolError("p must be 5 to 10007")
    if not _prime(p):
        raise ProtocolError("p must be prime")
    out = [p]
    for k, lo in (("g", 2), ("a", 1), ("b", 1)):
        v = data[k]
        if type(v) is not int:
            raise ProtocolError(k + " must be an int")
        if not lo <= v <= p - 2:
            raise ProtocolError("%s must be %d to p-2" % (k, lo))
        out.append(v)
    return out


def dh_exchange(data):
    p, g, a, b = _validate(data)
    pub_a = pow(g, a, p)
    pub_b = pow(g, b, p)
    sh_a = pow(pub_b, a, p)
    sh_b = pow(pub_a, b, p)
    x = None
    cur = 1
    for e in range(1, p):
        cur = cur * g % p
        if cur == pub_a:
            x = e
            break
    rec = pow(pub_b, x, p) if x is not None else None
    return {
        "status": "completed",
        "public_a": pub_a,
        "public_b": pub_b,
        "shared_a": sh_a,
        "shared_b": sh_b,
        "agree": sh_a == sh_b,
        "recovered_exponent": x,
        "recovered_shared": rec,
        "attack_matches": rec == sh_a,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
