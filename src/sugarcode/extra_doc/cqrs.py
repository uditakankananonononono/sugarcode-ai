"""Row 649, CQRS: separate write model and read model over an event log.

A tiny account ledger. The write side validates each command against its own
balances and appends events; the read side is a projection rebuilt from the
events only. Withdrawals that would overdraw are rejected and emit no event.
Caps (checked before any work): at most 50 commands, account names of 1 to 16
characters, amounts nonbool ints from 1 to 1000000.
NOT_CLAIMED: eventual-consistency lag, concurrency, durable storage, snapshots,
event versioning, any message broker, production readiness.
"""
SCOPE = 'PARTIAL: single-process deterministic ledger; write model, event log and one projection only'
NOT_CLAIMED = ('eventual consistency lag', 'concurrency', 'durable storage', 'snapshots',
               'event versioning', 'message broker', 'production readiness')
MAX_COMMANDS = 50


def _check(commands):
    if type(commands) not in (list, tuple):
        raise TypeError('commands must be a list or tuple')
    if len(commands) > MAX_COMMANDS:
        raise ValueError('commands must contain at most 50 entries')
    for c in commands:
        if type(c) not in (list, tuple) or len(c) != 3:
            raise ValueError('each command must be an (operation, account, amount) triple')
        op, acct, amt = c
        if type(op) is not str or op not in ('deposit', 'withdraw'):
            raise ValueError('operation must be deposit or withdraw')
        if type(acct) is not str or not 1 <= len(acct) <= 16:
            raise ValueError('account must be a string of 1 to 16 characters')
        if type(amt) is not int or not 1 <= amt <= 1000000:
            raise ValueError('amount must be a nonbool integer between 1 and 1000000')


def project(events):
    """Read model: balances per account, rebuilt from events alone."""
    view = {}
    for e in events:
        sign = 1 if e['kind'] == 'deposited' else -1
        view[e['account']] = view.get(e['account'], 0) + sign * e['amount']
    return view


def run_cqrs(commands):
    _check(commands)
    balances, events, rejected = {}, [], []
    for i, (op, acct, amt) in enumerate(commands):
        have = balances.get(acct, 0)
        if op == 'withdraw' and amt > have:
            rejected.append((i, 'insufficient funds'))
            continue
        balances[acct] = have + amt if op == 'deposit' else have - amt
        events.append({'seq': len(events), 'account': acct,
                       'kind': 'deposited' if op == 'deposit' else 'withdrawn', 'amount': amt})
    return {'events': events, 'read_model': project(events), 'rejected': rejected,
            'command_count': len(commands)}
