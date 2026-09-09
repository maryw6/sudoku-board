import argparse
import sys

from .board import BoardParseError, find_conflicts, parse
from .printer import format_json, format_pretty
from .solver import UnsolvableError, solve


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sudoku-board",
        description="Parse, validate, print, and solve a sudoku board.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="path to a puzzle file (defaults to stdin)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of the printed grid",
    )
    parser.add_argument(
        "--solve",
        action="store_true",
        help="print a completed solution instead of the clues as given",
    )
    args = parser.parse_args(argv)

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    try:
        board = parse(text)
    except BoardParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    conflicts = find_conflicts(board)

    if args.solve:
        try:
            board = solve(board)
        except UnsolvableError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        conflicts = []

    output = format_json(board, conflicts) if args.json else format_pretty(board, conflicts)
    print(output)
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
