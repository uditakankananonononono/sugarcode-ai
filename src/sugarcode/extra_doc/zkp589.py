"""Doc row589 Zero-Knowledge Proof: PARTIAL toy Schnorr transcript equation.

Fixed toy group p=23, q=11, g=2. Check g**response == commitment *
public**challenge (mod p). Public/commitment are nonidentity subgroup members;
challenge/response exact nonbool integers0..10. Returns equation validity only.
No witness generation, randomness, zero-knowledge proof, authentication,
noninteractive challenge generation or cryptographic security is claimed.
Parameters are tiny and deliberately insecure; never use for real secrets.
"""


def check(public, commitment, challenge, response):
    for value in (public, commitment):
        if type(value) is not int or not 2 <= value <= 22 or pow(value, 11, 23) != 1:
            raise ValueError('public and commitment must be nonidentity members of the toy subgroup')
    for value in (challenge, response):
        if type(value) is not int or not 0 <= value <= 10:
            raise ValueError('challenge and response must be integers in 0..10')
    valid = pow(2, response, 23) == commitment * pow(public, challenge, 23) % 23
    return {'equation_valid': valid, 'claim': 'PARTIAL', 'security_validated': False}
