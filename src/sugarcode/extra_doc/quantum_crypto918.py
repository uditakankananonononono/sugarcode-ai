"""Quantum Cryptography - Unbreakable encryption.

PARTIAL: deterministic BB84 transcript sifting/error audit, not encryption or a
secure key generator. No quantum channel, authenticated transport, privacy
amplification, finite-key proof or claim of unbreakable encryption.
"""


def audit_bb84(alice_bits, alice_bases, bob_bits, bob_bases, disclosed):
    """Sift equal bases, disclose selected sifted positions, calculate exact QBER.

    All four binary sequences must be exact lists/tuples, equal length 1..10000;
    entries are exact built-in ints. `disclosed` contains unique transmission
    indices within sifted positions, in any order; at least one is required.
    Returns exact numerator/denominator and remaining *candidate* bits. Never
    promotes candidates to secure key material, even if observed QBER is zero.
    """
    sequences=(alice_bits,alice_bases,bob_bits,bob_bases)
    for seq in sequences:
        if type(seq) not in (list,tuple) or not 1<=len(seq)<=10000:
            raise ValueError('binary sequences must be lists/tuples of length 1..10000')
        for bit in seq:
            if type(bit) is not int or bit not in (0,1):
                raise ValueError('binary entries must be built-in int 0 or 1')
    if len({len(seq) for seq in sequences})!=1:
        raise ValueError('binary sequences must have equal lengths')
    sifted=tuple(i for i in range(len(alice_bits)) if alice_bases[i]==bob_bases[i])
    if type(disclosed) not in (list,tuple) or not disclosed:
        raise ValueError('nonempty disclosed list/tuple required')
    for index in disclosed:
        if type(index) is not int or index not in sifted:
            raise ValueError('disclosed indices must be built-in ints in sifted positions')
    if len(set(disclosed))!=len(disclosed):
        raise ValueError('disclosed indices must be unique')
    errors=sum(alice_bits[i]!=bob_bits[i] for i in disclosed)
    remaining=tuple(i for i in sifted if i not in set(disclosed))
    return {'sifted_indices':sifted,'disclosed_indices':tuple(sorted(disclosed)),
            'error_count':errors,'sample_size':len(disclosed),'qber':errors/len(disclosed),
            'candidate_indices':remaining,'alice_candidate':tuple(alice_bits[i] for i in remaining),
            'bob_candidate':tuple(bob_bits[i] for i in remaining),
            'secure_key':False,'scope':'BB84 transcript audit only; candidate bits are not secure keys'}
