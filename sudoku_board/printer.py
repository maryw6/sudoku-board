"""Turning a Board into something a person or a program can consume."""

import json

from .board import BOX_SIZE, EMPTY, SIZE, find_conflicts

_ROW_SEPARATOR = "+-------+-------+-------+"


def format_pretty(board, conflicts=None):
    """Render the board as a boxed grid, with any conflicts listed below."""
    if conflicts is None:
        conflicts = find_conflicts(board)

    lines = [_ROW_SEPARATOR]
    for r in range(SIZE):
        cells = []
        for c in range(SIZE):
            value = board.cells[r][c]
            cells.append(str(value) if value != EMPTY else ".")
            if c % BOX_SIZE == 2 and c != SIZE - 1:
                cells.append("|")
        lines.append("| " + " ".join(cells) + " |")
        if r % BOX_SIZE == 2:
            lines.append(_ROW_SEPARATOR)
    grid = "\n".join(lines)

    if not conflicts:
        return grid
    return grid + "\n\n" + "\n".join(_describe(c) for c in conflicts)


def _describe(conflict):
    where = f"{conflict.kind} {conflict.index + 1}"
    cells = ", ".join(f"r{r + 1}c{c + 1}" for r, c in conflict.cells)
    return f"duplicate {conflict.value} in {where}: {cells}"


def format_json(board, conflicts=None):
    """Render the board as JSON: cells, overall validity, and conflicts."""
    if conflicts is None:
        conflicts = find_conflicts(board)

    payload = {
        "cells": board.cells,
        "valid": not conflicts,
        "conflicts": [
            {
                "kind": c.kind,
                "index": c.index,
                "value": c.value,
                "cells": [{"row": r, "col": col} for r, col in c.cells],
            }
            for c in conflicts
        ],
    }
    return json.dumps(payload, indent=2)
