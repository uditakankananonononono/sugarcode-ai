"""Row 576, Game Engine (PARTIAL: one fixed rule set, solved exactly): who wins a game of Nim with a take limit, and how.

solve_nim(piles, max_take) plays out the game of Nim in which two players alternate; on a turn the player picks one pile
and removes between 1 and max_take items from it (not more than the pile holds); the player who cannot move loses.
It searches every reachable position exhaustively, so the answer is exact, and returns:
  winner         'first' when the player to move can force a win, otherwise 'second';
  winning_moves  every move [pile_index, take] that leaves the opponent in a lost position, sorted; empty when
                 the player to move loses;
  move           the first of winning_moves, or None.
Caps: piles a list or tuple of 1 to 4 nonbool ints, each 0 to 12; max_take a nonbool int from 1 to 12.
Order of checks: piles (type, count, then each value in order: type, range), then max_take (type, range), and only then
the search.

NOT_CLAIMED: the solution of one abstract rule set. It does not make a game fun, fair or playable, does not play
against a human, models no interface, and says nothing about any other game; the exhaustive search is the only method
used. No clinical or wet-lab claim.
"""

MAX_PILES = 4
MAX_PILE = 12
MAX_TAKE = 12


def _int(v, what):
    if type(v) is not int:
        raise TypeError(what + ' must be a nonbool int')
    return v


def solve_nim(piles, max_take):
    if type(piles) not in (list, tuple):
        raise TypeError('piles must be a list or tuple')
    if not 1 <= len(piles) <= MAX_PILES:
        raise ValueError('pile count must be between 1 and 4')
    ps = []
    for p in piles:
        v = _int(p, 'pile')
        if not 0 <= v <= MAX_PILE:
            raise ValueError('pile must be between 0 and 12')
        ps.append(v)
    k = _int(max_take, 'max_take')
    if not 1 <= k <= MAX_TAKE:
        raise ValueError('max_take must be between 1 and 12')
    memo = {}

    def mover_wins(state):
        if state not in memo:
            win = False
            for i, n in enumerate(state):
                for t in range(1, min(k, n) + 1):
                    nxt = state[:i] + (n - t,) + state[i + 1:]
                    if not mover_wins(nxt):
                        win = True
            memo[state] = win
        return memo[state]
    start = tuple(ps)
    moves = []
    for i, n in enumerate(start):
        for t in range(1, min(k, n) + 1):
            if not mover_wins(start[:i] + (n - t,) + start[i + 1:]):
                moves.append([i, t])
    return {'winner': 'first' if moves else 'second', 'winning_moves': moves, 'move': moves[0] if moves else None}
