"""Row 525: Authentication Design - Verifies identity.

SCOPED planning aid over caller supplied rows. No external actions, persistence,
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


def verify_challenge_signature(row):
    """Tuple: (Ed25519 public_key bytes32, challenge bytes16..256, signature bytes64).

    Cryptographically verify possession evidence for this exact challenge/key.
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
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, challenge)
    except InvalidSignature:
        return False
    return True
