"""Row 525: Authentication Design - Verifies identity.

Bounded planning aid over caller supplied rows. No external actions, persistence,
capability development evidence, organization quality, or optimal policy claim.
Explicit import only; 1..32 tuple rows. Labels are lowercase ASCII identifiers.
"""
import re

LABEL = re.compile(r"[a-z][a-z0-9_]{0,23}\Z")


def _label(value):
    if type(value) is not str:
        raise TypeError('exact string label required')
    if len(value) > 24 or LABEL.fullmatch(value) is None:
        raise ValueError('label must be 1..24 lowercase identifier characters')


def _integer(value, low, high):
    if type(value) is not int:
        raise TypeError('exact nonbool integer required')
    if not low <= value <= high:
        raise ValueError('integer outside declared range')


def _rows(rows, arity):
    if type(rows) is not list:
        raise TypeError('exact list required')
    if not 1 <= len(rows) <= 32:
        raise ValueError('row count must be 1..32')
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple row required')
        if len(row) != arity:
            raise ValueError('wrong row arity')


def evaluate_authentication(rows):
    """Rows: (subject, primary_verified_bit, second_verified_bit, require_second_bit).
    Pure decision over caller verified assertions. Does not authenticate real
    identities, check passwords, issue sessions or establish identity trust.
    """
    _rows(rows, 4)
    for subject, primary, second, required in rows:
        _label(subject)
        _integer(primary, 0, 1)
        _integer(second, 0, 1)
        _integer(required, 0, 1)
    if len({x[0] for x in rows}) != len(rows):
        raise ValueError('duplicate subject')
    return {'decisions': [(subject, primary==1 and (required==0 or second==1))
                          for subject,primary,second,required in sorted(rows)]}


_SMALL_ORDER_PUBLIC_KEYS = frozenset(bytes.fromhex(value) for value in (
    '0100000000000000000000000000000000000000000000000000000000000000',
    'c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a',
    '0000000000000000000000000000000000000000000000000000000000000080',
    '26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05',
    'ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f',
    '26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85',
    '0000000000000000000000000000000000000000000000000000000000000000',
    'c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa',
))


def _small_order_public_key(encoded):
    # Normalize field aliases too; sign is irrelevant for the two x=0 points.
    bits = int.from_bytes(encoded, 'little')
    y = (bits & (2**255 - 1)) % (2**255 - 19)
    sign = bits >> 255
    if y in (1, 2**255 - 20):
        sign = 0
    normalized = (y | (sign << 255)).to_bytes(32, 'little')
    return normalized in _SMALL_ORDER_PUBLIC_KEYS


def verify_challenge_signature(row):
    """Tuple: (Ed25519 public_key bytes32, challenge bytes16..256, signature bytes64).

    Verify an Ed25519 signature for this exact challenge/key, rejecting small-order
    public keys. Signature validity alone does not establish identity or enrollment.
    The caller must bind the public key through trusted enrollment, issue a fresh
    unpredictable challenge and consume it once. This stateless helper does NOT
    verify a person's identity, challenge freshness, audience or replay status.
    No credentials, enrollment, account lookup or sessions are stored.
    Requires the existing cryptography vault/dev optional dependency.
    """
    if type(row) is not tuple:
        raise TypeError('exact tuple proof required')
    if len(row) != 3:
        raise ValueError('proof arity must be three')
    for value in row:
        if type(value) is not bytes:
            raise TypeError('exact proof bytes required')
    public_key, challenge, signature = row
    if len(public_key) != 32 or not 16 <= len(challenge) <= 256 or len(signature) != 64:
        raise ValueError('proof byte lengths outside declared range')
    if _small_order_public_key(public_key):
        raise ValueError('small-order public key refused')
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, challenge)
    except InvalidSignature:
        return False
    return True
