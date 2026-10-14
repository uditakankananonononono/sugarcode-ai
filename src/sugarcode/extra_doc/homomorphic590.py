"""Row 590 Homomorphic Encryption - Computes on encrypted data.

Bounded Paillier ciphertext multiplication/addition and nonnegative scalar
multiplication on supplied ciphertexts. No key generation, encryption or
private-key access. The caller must validate the key and ciphertext provenance.
A modulus is accepted syntactically, not proved semiprime or secure. Bounded
reference arithmetic, not constant-time or production cryptographic service.
"""
import math


def _integer(value,low,high):
    if type(value) is not int:
        raise TypeError('exact nonbool integer required')
    if not low<=value<=high:
        raise ValueError('integer outside declared range')


def combine_ciphertexts(modulus, rows):
    """Rows (ciphertext, nonnegative_weight). Return product(c**weight) mod n².
    For valid Paillier ciphertexts this encrypts the weighted plaintext sum mod n.
    n3..2**4096; 1..32rows; weights0..1024. Ciphertexts must be units mod n².
    """
    _integer(modulus,3,2**4096)
    if type(rows) is not list:
        raise TypeError('exact list required')
    if not 1<=len(rows)<=32:
        raise ValueError('row count must be 1..32')
    square=modulus*modulus
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple row required')
        if len(row)!=2:
            raise ValueError('row arity must be two')
        ciphertext,weight=row
        _integer(ciphertext,1,square-1)
        _integer(weight,0,1024)
        if math.gcd(ciphertext,modulus)!=1:
            raise ValueError('ciphertext must be a unit modulo modulus')
    result=1
    for ciphertext,weight in rows:
        result=result*pow(ciphertext,weight,square)%square
    return result
