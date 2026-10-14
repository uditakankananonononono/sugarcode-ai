"""Game Engine - exact rule engine for one specified grid game (move script replay).

Pure function over caller data. No rendering, no input devices, no network, no clock, no
randomness. Input: grid, 1..20 equal-length strings of 1..20 characters from '.' floor,
'#' wall, '@' start (exactly one), 'o' coin, 'G' goal (0..1); moves, a string of 0..500
characters from U D L R.

Rules: the player starts on '@'. Each move goes one cell up, down, left or right. A move
into a wall or off the grid is blocked: the player stays and the blocked counter rises.
Entering a coin cell collects the coin (the cell becomes floor). Entering the goal ends
the game; every later move is ignored and counted as ignored. The result reports final
row and column, coins collected, coins left, moves applied (moved or blocked, before the
game ended), blocked, ignored, and whether the goal was reached.

Scope: PARTIAL for the Game Engine line. Exact replay of one tiny rule set. It is not a
game framework: no graphics, no real-time loop, no AI opponents, no physics.

Not claimed: that the game is fun or playable by people, that the script is a good
strategy, that the rules suit any other game, or anything about real interactive
products. Every claim flag in the result is False.
"""

MAX_SIDE = 20
MAX_MOVES = 500
_TOP = frozenset({"grid", "moves"})
_CELLS = frozenset(".#@oG")
_DELTA = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}

NOT_CLAIMED = (
    "the game is fun or playable by people",
    "the script is a good strategy",
    "the rules suit any other game",
    "real interactive product behaviour",
)
CLAIMS = {"fun": False, "good_strategy": False, "general_rules": False, "real_product": False}


class GameError(ValueError):
    pass


def _validate(data):
    if not isinstance(data, dict) or set(data) != _TOP:
        raise GameError("data keys must be exactly grid, moves")
    g = data["grid"]
    if not isinstance(g, list) or not 1 <= len(g) <= MAX_SIDE:
        raise GameError("grid must be a list of 1..20 strings")
    for r in g:
        if not type(r) is str:
            raise GameError("grid rows must be strings")
    w = len(g[0])
    if not 1 <= w <= MAX_SIDE:
        raise GameError("grid width must be 1..20")
    for r in g:
        if len(r) != w:
            raise GameError("grid rows must have equal length")
        if any(ch not in _CELLS for ch in r):
            raise GameError("grid has an unknown cell character")
    flat = "".join(g)
    if flat.count("@") != 1:
        raise GameError("grid must have exactly one start")
    if flat.count("G") > 1:
        raise GameError("grid must have at most one goal")
    mv = data["moves"]
    if not type(mv) is str:
        raise GameError("moves must be a string")
    if len(mv) > MAX_MOVES:
        raise GameError("moves too long")
    if any(c not in _DELTA for c in mv):
        raise GameError("moves must use only U D L R")
    return g, mv


def game_engine(data):
    g, mv = _validate(data)
    cells = [list(r) for r in g]
    h, w = len(cells), len(cells[0])
    pr = pc = 0
    for i in range(h):
        for j in range(w):
            if cells[i][j] == "@":
                pr, pc = i, j
                cells[i][j] = "."
    coins = blocked = applied = ignored = 0
    won = False
    for c in mv:
        if won:
            ignored += 1
            continue
        dr, dc = _DELTA[c]
        nr, nc = pr + dr, pc + dc
        applied += 1
        if not (0 <= nr < h and 0 <= nc < w) or cells[nr][nc] == "#":
            blocked += 1
            continue
        pr, pc = nr, nc
        if cells[pr][pc] == "o":
            coins += 1
            cells[pr][pc] = "."
        elif cells[pr][pc] == "G":
            won = True
    left = sum(r.count("o") for r in cells)
    return {
        "status": "completed",
        "row": pr,
        "column": pc,
        "coins_collected": coins,
        "coins_left": left,
        "moves_applied": applied,
        "blocked": blocked,
        "ignored": ignored,
        "goal_reached": won,
        "claims": dict(CLAIMS),
        "not_claimed": list(NOT_CLAIMED),
    }
