"""Row 123 Reproducibility Verification - Checks if results can be recreated.

PARTIAL: exact ordered artifact Merkle-root comparison across two supplied runs.
Input exact dict original and repeated, each an exact list of 1..8 exact strings
of 0..12 printable ASCII characters (space through tilde). Artifact order matters.
Leaf digest SHA256(b'leaf:' + artifact.encode('ascii')); internal digest
SHA256(b'node:' + left_digest_bytes + right_digest_bytes). Duplicate the last
node at every odd-width level until one root remains. Return roots as two lower
hex strings, equal as root equality boolean, changed as ordered positions whose
artifact strings differ or exist in only one run, claims three False booleans.
This compares supplied output bytes only, without executing code, reading files,
checking environment/provenance, or proving actual scientific reproducibility.
Equal roots do not prove equal artifact lists: odd-node duplication can hide
a repeated suffix (for example [a,b,c] versus [a,b,c,c]); changed is authoritative
for artifact-list differences.
NOT_CLAIMED: result recreation, provenance verification, equality of artifact lists
from equal roots, production readiness.
"""
from hashlib import sha256
SCOPE = 'PARTIAL: supplied ordered artifact Merkle-root comparison only'
NOT_CLAIMED = ('result recreation', 'provenance verification', 'equality of artifact lists from equal roots', 'production readiness')


def _root(artifacts):
    level = [sha256(b'leaf:' + item.encode('ascii')).digest() for item in artifacts]
    while len(level) > 1:
        if len(level) % 2:
            level = level + [level[-1]]
        level = [sha256(b'node:' + level[i] + level[i+1]).digest() for i in range(0, len(level), 2)]
    return level[0].hex()


def compare(data):
    if type(data) is not dict or set(data) != {'original', 'repeated'}:
        raise ValueError('exact dict with original and repeated required')
    for name in ('original', 'repeated'):
        rows = data[name]
        if type(rows) is not list or not 1 <= len(rows) <= 8:
            raise ValueError(name + ' must be an exact list of 1..8 artifacts')
        for value in rows:
            if type(value) is not str or len(value) > 12 or any(not ' ' <= c <= '~' for c in value):
                raise ValueError('artifacts must be exact printable ASCII strings of length 0..12')
    original, repeated = data['original'], data['repeated']
    roots = [_root(original), _root(repeated)]
    changed = [i for i in range(max(len(original), len(repeated))) if i >= len(original) or i >= len(repeated) or original[i] != repeated[i]]
    return {'roots': roots, 'equal': roots[0] == roots[1], 'changed': changed, 'claims': [False, False, False]}
