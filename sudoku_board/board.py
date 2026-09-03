"""Parsing and rule-checking for 9x9 sudoku boards.

A Board only stores the digits that were given; it does not know how to
solve a puzzle. What it can do is tell you whether the clues it was
handed already break the one rule sudoku has: no digit twice in a row,
column, or 3x3 box.
"""

from dataclasses import dataclass

SIZE = 9
BOX_SIZE = 3
EMPTY = 0
_EMPTY_CHARS = {".", "0", "_"}
_DIGIT_CHARS = set("123456789")


class BoardError(Exception):
    """Base class for problems with a sudoku board."""


class BoardParseError(BoardError):
    """Raised when input text cannot be read as an 81-cell board."""


class Board:
    __slots__ = ("cells",)

    def __init__(self, cells):
        # cells is a 9x9 list of lists, 0 meaning empty.
        self.cells = cells

    def __eq__(self, other):
        return isinstance(other, Board) and self.cells == other.cells

    def row(self, index):
        return list(self.cells[index])

    def column(self, index):
        return [self.cells[r][index] for r in range(SIZE)]

    def box(self, index):
        # Boxes are numbered left-to-right, top-to-bottom: 0..8.
        top = (index // BOX_SIZE) * BOX_SIZE
        left = (index % BOX_SIZE) * BOX_SIZE
        return [
            self.cells[r][c]
            for r in range(top, top + BOX_SIZE)
            for c in range(left, left + BOX_SIZE)
        ]


def parse(text):
    """Parse an 81-cell board out of arbitrary text.

    Digits 1-9 are clues; '.', '0', or '_' are blanks. All whitespace is
    ignored, which is what lets both a single 81-character line and a
    9-line visual grid work as input.
    """
    values = []
    for i, ch in enumerate(text):
        if ch.isspace():
            continue
        if ch in _EMPTY_CHARS:
            values.append(EMPTY)
        elif ch in _DIGIT_CHARS:
            values.append(int(ch))
        else:
            raise BoardParseError(f"unexpected character {ch!r} at position {i}")

    if len(values) != SIZE * SIZE:
        raise BoardParseError(
            f"expected {SIZE * SIZE} cells, found {len(values)}"
        )

    cells = [values[r * SIZE:(r + 1) * SIZE] for r in range(SIZE)]
    return Board(cells)


@dataclass(frozen=True)
class Conflict:
    kind: str  # "row", "column", or "box"
    index: int  # 0-based index of the unit
    value: int
    cells: tuple  # (row, col) 0-based positions that clash


def find_conflicts(board):
    """Return every place two equal digits share a row, column, or box."""
    conflicts = []
    units = (
        ("row", board.row),
        ("column", board.column),
        ("box", board.box),
    )
    for kind, unit_at in units:
        for i in range(SIZE):
            positions_by_value = {}
            for pos, value in enumerate(unit_at(i)):
                if value == EMPTY:
                    continue
                positions_by_value.setdefault(value, []).append(pos)
            for value, positions in positions_by_value.items():
                if len(positions) > 1:
                    cells = tuple(
                        _unit_position_to_cell(kind, i, pos) for pos in positions
                    )
                    conflicts.append(Conflict(kind, i, value, cells))
    return conflicts


def _unit_position_to_cell(kind, index, pos):
    if kind == "row":
        return (index, pos)
    if kind == "column":
        return (pos, index)
    top = (index // BOX_SIZE) * BOX_SIZE
    left = (index % BOX_SIZE) * BOX_SIZE
    return (top + pos // BOX_SIZE, left + pos % BOX_SIZE)


def is_valid(board):
    return not find_conflicts(board)
