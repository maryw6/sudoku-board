"""Backtracking solver for boards whose clues don't already conflict."""

from .board import BOX_SIZE, EMPTY, SIZE, Board, is_valid


class UnsolvableError(Exception):
    """Raised when a board has no valid completion."""


def solve(board):
    """Return a new, fully filled Board that respects all of the clues.

    Raises UnsolvableError if the clues already conflict, or if there is
    no way to fill the remaining cells without breaking a rule. A board
    with more than one solution just gets whichever one the search finds
    first.
    """
    if not is_valid(board):
        raise UnsolvableError("board has conflicting clues")

    cells = [list(row) for row in board.cells]
    rows = [set() for _ in range(SIZE)]
    cols = [set() for _ in range(SIZE)]
    boxes = [set() for _ in range(SIZE)]

    empties = []
    for r in range(SIZE):
        for c in range(SIZE):
            value = cells[r][c]
            if value == EMPTY:
                empties.append((r, c))
            else:
                rows[r].add(value)
                cols[c].add(value)
                boxes[_box_index(r, c)].add(value)

    if _fill(cells, rows, cols, boxes, empties, 0):
        return Board(cells)
    raise UnsolvableError("no solution exists for these clues")


def _box_index(r, c):
    return (r // BOX_SIZE) * BOX_SIZE + (c // BOX_SIZE)


def _fill(cells, rows, cols, boxes, empties, i):
    if i == len(empties):
        return True
    r, c = empties[i]
    b = _box_index(r, c)
    for value in range(1, SIZE + 1):
        if value in rows[r] or value in cols[c] or value in boxes[b]:
            continue
        cells[r][c] = value
        rows[r].add(value)
        cols[c].add(value)
        boxes[b].add(value)
        if _fill(cells, rows, cols, boxes, empties, i + 1):
            return True
        cells[r][c] = EMPTY
        rows[r].discard(value)
        cols[c].discard(value)
        boxes[b].discard(value)
    return False
