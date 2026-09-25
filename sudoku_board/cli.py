import argparse
import json
import sys
import urllib.request

from .board import BoardParseError, find_conflicts, parse, parse_warnings
from .printer import format_json, format_pretty
from .solver import UnsolvableError, solve

_URL_PREFIXES = ("http://", "https://")


def _read_source(source):
    """Read puzzle text from a local file path or an http(s) URL.

    URLError (including HTTPError) is a subclass of OSError, so callers
    can catch OSError the same way whether the source turned out to be a
    file or a URL.
    """
    if source.startswith(_URL_PREFIXES):
        with urllib.request.urlopen(source, timeout=10) as response:
            return response.read().decode("utf-8")
    with open(source, "r", encoding="utf-8") as f:
        return f.read()


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sudoku-board",
        description="Parse, validate, print, and solve a sudoku board.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help=(
            "one or more puzzle sources: file paths, http(s) URLs, or "
            "omitted to read from stdin"
        ),
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
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat parse warnings (e.g. too few clues) as errors",
    )
    args = parser.parse_args(argv)

    if len(args.files) > 1:
        return _run_many(args.files, args)
    return _run_one(args.files[0] if args.files else None, args)


def _run_one(path, args):
    """Original single-board behavior: no filename headers in the output."""
    if path:
        try:
            text = _read_source(path)
        except OSError as exc:
            print(f"error: {path}: {exc.strerror or exc}", file=sys.stderr)
            return 1
    else:
        text = sys.stdin.read()

    try:
        board = parse(text)
    except BoardParseError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    warnings = parse_warnings(board)
    if warnings and args.strict:
        for warning in warnings:
            print(f"error: {warning}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)

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


def _run_many(paths, args):
    """Process several files in one invocation, one board per path.

    A bad file (parse error, strict warning, unsolvable) doesn't stop the
    rest from being processed - it's reported and the run's exit code
    reflects that something failed, same as if it were the only file.
    """
    entries = []
    failed = False

    for path in paths:
        try:
            text = _read_source(path)
        except OSError as exc:
            print(f"error: {path}: {exc.strerror or exc}", file=sys.stderr)
            entries.append({"file": path, "error": str(exc.strerror or exc)})
            failed = True
            continue

        try:
            board = parse(text)
        except BoardParseError as exc:
            print(f"error: {path}: {exc}", file=sys.stderr)
            entries.append({"file": path, "error": str(exc)})
            failed = True
            continue

        warnings = parse_warnings(board)
        if warnings and args.strict:
            for warning in warnings:
                print(f"error: {path}: {warning}", file=sys.stderr)
            entries.append({"file": path, "error": "; ".join(warnings)})
            failed = True
            continue
        for warning in warnings:
            print(f"warning: {path}: {warning}", file=sys.stderr)

        conflicts = find_conflicts(board)

        if args.solve:
            try:
                board = solve(board)
            except UnsolvableError as exc:
                print(f"error: {path}: {exc}", file=sys.stderr)
                entries.append({"file": path, "error": str(exc)})
                failed = True
                continue
            conflicts = []

        if conflicts:
            failed = True
        entries.append({"file": path, "board": board, "conflicts": conflicts})

    if args.json:
        payloads = []
        for entry in entries:
            if "error" in entry:
                payloads.append({"file": entry["file"], "error": entry["error"]})
            else:
                payload = json.loads(format_json(entry["board"], entry["conflicts"]))
                payloads.append({"file": entry["file"], **payload})
        print(json.dumps(payloads, indent=2))
    else:
        blocks = []
        for entry in entries:
            if "error" in entry:
                blocks.append(f"== {entry['file']} ==\nerror: {entry['error']}")
            else:
                blocks.append(
                    f"== {entry['file']} ==\n"
                    + format_pretty(entry["board"], entry["conflicts"])
                )
        print("\n\n".join(blocks))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
