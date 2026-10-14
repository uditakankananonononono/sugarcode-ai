"""Row 591 Secure Multi-Party Computation - Computes jointly.

Bounded local additive-share sum arithmetic modulo caller supplied modulus.
Every share is present in this process: this simulator provides NO secrecy,
party isolation, authenticated communication or malicious-party security.
It must not be used as a secure multi-party computation deployment.
"""


def _integer(value,low,high):
    if type(value) is not int:
        raise TypeError('exact nonbool integer required')
    if not low<=value<=high:
        raise ValueError('integer outside declared range')


def sum_shared_values(modulus,rows):
    """Each row is a tuple of 2..8 party shares, every row has same arity.
    1..32 shared inputs, each share0..modulus-1, modulus2..1,000,003.
    Return per-party aggregated shares and reconstructed modular sum.
    """
    _integer(modulus,2,1000003)
    if type(rows) is not list:
        raise TypeError('exact list required')
    if not 1<=len(rows)<=32:
        raise ValueError('row count must be 1..32')
    arity=None
    for row in rows:
        if type(row) is not tuple:
            raise TypeError('exact tuple row required')
        if not 2<=len(row)<=8:
            raise ValueError('share row arity must be 2..8')
        if arity is None:
            arity=len(row)
        elif len(row)!=arity:
            raise ValueError('share row arities must match')
        for share in row:
            _integer(share,0,modulus-1)
    totals=[sum(row[i] for row in rows)%modulus for i in range(arity)]
    return {'party_totals':totals,'reconstructed_sum':sum(totals)%modulus,'parties':arity,'inputs':len(rows)}
