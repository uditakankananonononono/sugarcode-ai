"""Bounded double-entry integer journal fixtures over caller-supplied data.

Accounts and line ids are exact ints 0..15 and 0..31. A journal is an exact
 tuple of at most32 (line_id, account, signed_minor_units) exact tuples.
Unique line ids, not unique accounts. Positive amounts mean debit, negative
credit. Amounts are exact ints with abs<=1000. Empty journal is allowed.
Balances are exact tuples of at most16 unique (account, balance) pairs,
abs(balance)<=32000. No currencies, dates, external records or accounting
policy inferred. Every input is validated before computing a result.
Validation order: outer type, length, all row shapes, all scalar types,
all scalar bounds in row order, duplicate ids, then semantic relations.
"""
SCOPE = 'PARTIAL bounded caller-supplied double-entry conservation and replay fixtures'
NOT_CLAIMED = ('AGI-like intelligence', 'accounting correctness', 'financial advice', 'currency compatibility', 'production readiness')
CLAIMS = {'agi_like_intelligence': False, 'production_ready': False, 'accounting_correctness': False}


def _fail(code):
    raise ValueError('J489:' + code)


def _int(value, label, lo, hi):
    if type(value) is not int:
        _fail('type:' + label)
    if not lo <= value <= hi:
        _fail('bound:' + label)


def _rows(rows, label, width, cap, bounds):
    if type(rows) is not tuple:
        _fail('type:' + label)
    if len(rows) > cap:
        _fail('length:' + label)
    if any(type(row) is not tuple or len(row) != width for row in rows):
        _fail('shape:' + label)
    if any(type(value) is not int for row in rows for value in row):
        _fail('type:' + label + ':entry')
    for row in rows:
        for value, (lo, hi) in zip(row, bounds):
            if not lo <= value <= hi:
                _fail('bound:' + label + ':entry')
    ids = [row[0] for row in rows]
    if len(ids) != len(set(ids)):
        _fail('duplicate:' + label)


def _journal(lines):
    _rows(lines, 'lines', 3, 32, ((0, 31), (0, 15), (-1000, 1000)))


def _balances(balances, label='balances'):
    _rows(balances, label, 2, 16, ((0, 15), (-32000, 32000)))


def journal_balance(lines):
    """Return (total debit, total credit magnitude, signed imbalance)."""
    _journal(lines)
    debit = sum(amount for _, _, amount in lines if amount > 0)
    credit = -sum(amount for _, _, amount in lines if amount < 0)
    return debit, credit, debit - credit


def journal_account_totals(lines):
    """Sorted (account,debit,credit,net), including zero-only accounts."""
    _journal(lines)
    out = {}
    for _, account, amount in lines:
        debit, credit = out.get(account, (0, 0))
        out[account] = (debit + max(0, amount), credit + max(0, -amount))
    return tuple((a, d, c, d-c) for a, (d, c) in sorted(out.items()))


def journal_trial_balance(balances):
    """Return (sorted debit pairs, sorted credit magnitude pairs, imbalance).

    Zero accounts are omitted from the two sides, not from the imbalance.
    """
    _balances(balances)
    debit = tuple(sorted((a, b) for a, b in balances if b > 0))
    credit = tuple(sorted((a, -b) for a, b in balances if b < 0))
    return debit, credit, sum(b for _, b in balances)


def journal_post(balances, lines):
    """Post a balanced journal to declared accounts; sorted resulting balances.

    Output balance cap64000, input opening cap32000, journal total abs<=32000.
    """
    _balances(balances)
    _journal(lines)
    out = dict(balances)
    if any(a not in out for _, a, _ in lines):
        _fail('unknown:account')
    if sum(v for _, _, v in lines):
        _fail('unbalanced:lines')
    for _, a, v in lines:
        out[a] += v
    return tuple(sorted(out.items()))


def journal_reverse(lines):
    """Reverse sign of each line, preserving caller line order and ids."""
    _journal(lines)
    return tuple((i, a, -v) for i, a, v in lines)


def journal_reclassify(lines, source, target):
    """Move every source posting to target; source!=target; retain ids/order."""
    _journal(lines)
    _int(source, 'source', 0, 15)
    _int(target, 'target', 0, 15)
    if source == target:
        _fail('same:account')
    return tuple((i, target if a == source else a, v) for i, a, v in lines)


def journal_close_nominal(balances, nominal, equity):
    """Return closing (account,signed delta) pairs, not capped journal lines.

    Exact nominal tuple, at most15 unique ids; equity declared and not nominal.
    Nominal accounts close to zero and their net transfers to equity. Include
    all nominated accounts and equity, including zero deltas. Output<=480000.
    """
    _balances(balances)
    if type(nominal) is not tuple:
        _fail('type:nominal')
    if len(nominal) > 15:
        _fail('length:nominal')
    if any(type(a) is not int for a in nominal):
        _fail('type:nominal:entry')
    if any(not 0 <= a <= 15 for a in nominal):
        _fail('bound:nominal:entry')
    if len(set(nominal)) != len(nominal):
        _fail('duplicate:nominal')
    _int(equity, 'equity', 0, 15)
    current = dict(balances)
    if equity not in current or any(a not in current for a in nominal):
        _fail('unknown:account')
    if equity in nominal:
        _fail('equity:nominal')
    out = {a: -current[a] for a in nominal}
    out[equity] = sum(current[a] for a in nominal)
    return tuple(sorted(out.items()))


def journal_running_balances(opening, journals):
    """Snapshots including opening, then at most8 balanced journals.

    All journal structure is validated before unknown-account/balance checks.
    Each snapshot sorted; output magnitude<=288000 by input caps.
    """
    _balances(opening)
    if type(journals) is not tuple:
        _fail('type:journals')
    if len(journals) > 8:
        _fail('length:journals')
    for lines in journals:
        _journal(lines)
    state = dict(opening)
    for lines in journals:
        if any(a not in state for _, a, _ in lines):
            _fail('unknown:account')
        if sum(v for _, _, v in lines):
            _fail('unbalanced:lines')
    result = [tuple(sorted(state.items()))]
    for lines in journals:
        for _, account, amount in lines:
            state[account] += amount
        result.append(tuple(sorted(state.items())))
    return tuple(result)


def journal_suspense_completion(lines, suspense):
    """Return (account, amount) completion pair, or None when balanced.

    This is a separate uncapped delta, not a line inserted into a full journal.
    Suspense id0..15, output signed amount<=32000.
    """
    _journal(lines)
    _int(suspense, 'suspense', 0, 15)
    imbalance = sum(amount for _, _, amount in lines)
    return (suspense, -imbalance) if imbalance else None


def journal_reconcile(current, target):
    """Sorted nonzero target-current deltas; require identical account sets
    and identical net totals. Output per-account abs<=64000.
    """
    _balances(current, 'current')
    _balances(target, 'target')
    left, right = dict(current), dict(target)
    if left.keys() != right.keys():
        _fail('mismatch:accounts')
    if sum(left.values()) != sum(right.values()):
        _fail('mismatch:total')
    return tuple((a, right[a]-left[a]) for a in sorted(left) if right[a] != left[a])
