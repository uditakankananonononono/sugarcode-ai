"""Row 445, Customer Success (PARTIAL: one exact health-score rule): check a supplied account-health list.

check_accounts(accounts) takes accounts as a list of 0 to 40 tuples (account, health, touch_days): account 1 to
24 lowercase identifier characters, health an exact integer 0 to 100, touch_days an exact integer 0 to 365
(days since the last touch). The rules, applied to each account i (0-based), are:
  health below 40, else (i, 'at_risk');
  health at least 80 with touch_days over 30, else (i, 'neglected_win').
It returns {'problems': sorted (index, code), 'accounts': sorted distinct accounts present, 'total': the account
count}.
Order of checks: accounts (list type, count, then each in order: tuple type, 3 items, account type and shape,
health type and range, touch_days type and range), and only then the rules.

NOT_CLAIMED: this checks supplied health scores against two attention bars. It does not say the accounts achieve
outcomes, that 40, 80 or 30 days are the right bars, or that any customer stayed. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_accounts(accounts):
    if type(accounts) is not list:
        raise TypeError('accounts must be an exact list')
    if len(accounts) > 40:
        raise ValueError('account count must be at most 40')
    for s in accounts:
        if type(s) is not tuple:
            raise TypeError('each account must be an exact tuple')
        if len(s) != 3:
            raise ValueError('each account must have 3 items')
        if type(s[0]) is not str:
            raise TypeError('account must be an exact string')
        if LABEL.fullmatch(s[0]) is None:
            raise ValueError('account must be 1 to 24 lowercase identifier characters')
        if type(s[1]) is not int:
            raise TypeError('health must be an exact integer')
        if not 0 <= s[1] <= 100:
            raise ValueError('health must be 0 to 100')
        if type(s[2]) is not int:
            raise TypeError('touch_days must be an exact integer')
        if not 0 <= s[2] <= 365:
            raise ValueError('touch_days must be 0 to 365')
    problems = []
    names = set()
    for i, (account, health, touch_days) in enumerate(accounts):
        if health < 40:
            problems.append((i, 'at_risk'))
        if health >= 80 and touch_days > 30:
            problems.append((i, 'neglected_win'))
        names.add(account)
    return {'problems': sorted(problems), 'accounts': sorted(names), 'total': len(accounts)}
