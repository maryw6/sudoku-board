"""Rough difficulty rating for a puzzle.

The rating comes from the weakest technique that gets a human solver all
the way to the end: naked singles only is "easy", needing hidden singles
is "medium", and a board that stalls on both is "hard" (it takes
pencil-mark techniques beyond singles, or outright guessing; this module
doesn't try to tell those apart). Clue count only nudges the result: a
board with few givens that singles alone can finish is rated one step up,
since there is less on the page to lean on.
"""

from dataclasses import dataclass

from .board import BOX_SIZE, EMPTY, SIZE, clue_count, is_valid
from .solver import UnsolvableError, solve

LEVELS = ("easy", "medium", "hard")

# Below this many clues a singles-only board is bumped from easy to medium.
FEW_CLUES = 26

_DIGITS = frozenset(range(1, SIZE + 1))


@dataclass(frozen=True)
class Difficulty:
    level: str  # one of LEVELS
    technique: str  # hardest technique needed: naked singles, hidden singles, backtracking
    clues: int


def _box_index(r, c):
    return (r // BOX_SIZE) * BOX_SIZE + (c // BOX_SIZE)


def _build_units():
    units = []
    for i in range(SIZE):
        units.append([(i, c) for c in range(SIZE)])
        units.append([(r, i) for r in range(SIZE)])
        top = (i // BOX_SIZE) * BOX_SIZE
        left = (i % BOX_SIZE) * BOX_SIZE
        units.append(
            [(top + dr, left + dc) for dr in range(BOX_SIZE) for dc in range(BOX_SIZE)]
        )
    return units


_UNITS = _build_units()


def _build_peers():
    peers = {}
    for r in range(SIZE):
        for c in range(SIZE):
            found = set()
            for unit in _UNITS:
                if (r, c) in unit:
                    found.update(unit)
            found.discard((r, c))
            peers[(r, c)] = found
    return peers


_PEERS = _build_peers()


def estimate_difficulty(board):
    """Rate a board whose clues don't conflict.

    Raises UnsolvableError if the clues conflict or no completion exists,
    since a rating for such a board would mean nothing.
    """
    if not is_valid(board):
        raise UnsolvableError("board has conflicting clues")

    clues = clue_count(board)
    candidates = {}
    for r in range(SIZE):
        for c in range(SIZE):
            if board.cells[r][c] != EMPTY:
                continue
            seen = {board.cells[pr][pc] for pr, pc in _PEERS[(r, c)]}
            candidates[(r, c)] = set(_DIGITS - seen)

    used_hidden = False
    while candidates:
        if any(not options for options in candidates.values()):
            raise UnsolvableError("no solution exists for these clues")
        move = _naked_single(candidates)
        if move is None:
            move = _hidden_single(candidates)
            if move is not None:
                used_hidden = True
        if move is None:
            break
        pos, value = move
        del candidates[pos]
        for peer in _PEERS[pos]:
            if peer in candidates:
                candidates[peer].discard(value)

    if candidates:
        # Stalled on singles; make sure there is a solution at all before
        # calling it hard rather than impossible.
        solve(board)
        return Difficulty("hard", "backtracking", clues)
    if used_hidden:
        return Difficulty("medium", "hidden singles", clues)
    level = "medium" if clues < FEW_CLUES else "easy"
    return Difficulty(level, "naked singles", clues)


def _naked_single(candidates):
    for pos, options in candidates.items():
        if len(options) == 1:
            return pos, next(iter(options))
    return None


def _hidden_single(candidates):
    for unit in _UNITS:
        open_cells = [pos for pos in unit if pos in candidates]
        for value in _DIGITS:
            spots = [pos for pos in open_cells if value in candidates[pos]]
            if len(spots) == 1:
                return spots[0], value
    return None
