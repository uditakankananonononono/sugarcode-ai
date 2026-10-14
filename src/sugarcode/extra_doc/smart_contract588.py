"""Doc row588 Smart Contract Development: PARTIAL offline escrow reducer.

Simulate exact-list events (deposit/release/refund, actor, amount). Initial state
is empty; one positive deposit by buyer funds it, then exactly that amount may
be released by arbiter to seller or refunded by arbiter to buyer. Terminal state
rejects further events. Report accepted/rejected indexes without side effects.
Amounts are nonbool integers1..1000000, actors exactly buyer/seller/arbiter;
0..100 events. Invalid shape/type rejects input, invalid transitions are reported.
No deployment, signing, on-chain security, wallet use or actual money transfer.
"""


def simulate(events):
    if type(events) is not list or len(events) > 100:
        raise ValueError('events must be an exact list with 0..100 entries')
    for row in events:
        if type(row) is not tuple or len(row) != 3:
            raise ValueError('event must be an operation, actor, amount tuple')
        op, actor, amount = row
        if type(op) is not str or op not in ('deposit', 'release', 'refund'):
            raise ValueError('operation must be deposit, release or refund')
        if type(actor) is not str or actor not in ('buyer', 'seller', 'arbiter'):
            raise ValueError('actor must be buyer, seller or arbiter')
        if type(amount) is not int or not 1 <= amount <= 1000000:
            raise ValueError('amount must be an integer in 1..1000000')
    state, balance, recipient = 'empty', 0, None
    accepted, rejected = [], []
    for i, (op, actor, amount) in enumerate(events):
        if state == 'empty' and op == 'deposit' and actor == 'buyer':
            state, balance = 'funded', amount
        elif state == 'funded' and op in ('release', 'refund') and actor == 'arbiter' and amount == balance:
            state, balance, recipient = 'released' if op == 'release' else 'refunded', 0, 'seller' if op == 'release' else 'buyer'
        else:
            rejected.append(i)
            continue
        accepted.append(i)
    return {'state': state, 'balance': balance, 'recipient': recipient,
            'accepted': accepted, 'rejected': rejected, 'claim': 'PARTIAL', 'money_moved': False}
