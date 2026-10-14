"""Row 527 Encryption Implementation - Protects data.

SCOPED AES-256-GCM using the existing cryptography dependency, not custom crypto.
Caller supplies a 32-byte key and 12-byte nonce. Each key/nonce pair MUST be unique
for every encryption, even across processes and calls. This stateless helper
cannot enforce that rule. No key storage, nonce generation or key lifecycle.
Explicit import only. No logs, persistence, networking or account actions.
"""
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def _bytes(value, low, high):
    if type(value) is not bytes:
        raise TypeError('exact bytes required')
    if not low <= len(value) <= high:
        raise ValueError('byte length outside declared range')


def _request(row, decrypt):
    if type(row) is not tuple:
        raise TypeError('exact tuple request required')
    if len(row) != 4:
        raise ValueError('request arity must be four')
    key, nonce, data, aad = row
    _bytes(key, 32, 32)
    _bytes(nonce, 12, 12)
    _bytes(data, 16 if decrypt else 0, 65552 if decrypt else 65536)
    _bytes(aad, 0, 4096)
    return key, nonce, data, aad


def encrypt(row):
    """Tuple: (key, nonce, plaintext, additional_authenticated_data).

    Returns ciphertext with the 16-byte authentication tag appended.
    Caller must never reuse nonce with the same key.
    """
    key, nonce, data, aad = _request(row, False)
    return AESGCM(key).encrypt(nonce, data, aad)


def decrypt(row):
    """Tuple: (key, nonce, ciphertext_with_tag, additional_authenticated_data).

    Invalid authentication raises cryptography.exceptions.InvalidTag, never
    unauthenticated plaintext. Requires matching key, nonce and AAD.
    """
    key, nonce, data, aad = _request(row, True)
    return AESGCM(key).decrypt(nonce, data, aad)
