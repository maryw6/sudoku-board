# sudoku-board

A small library and command-line tool for reading a sudoku board from
text, checking whether its given clues are actually legal, and printing
it back out either for a person or for another program.

Most "sudoku parser" snippets floating around only handle one input
shape (usually a single 81-character line) and assume the input is
already valid. This one accepts a couple of common shapes, tells you
exactly which clues collide when they don't, and gives you the result
as JSON when you need to feed it to something else instead of your
own eyes.

## Install

No dependencies, nothing to build. Either run it in place:

```
python -m sudoku_board.cli puzzle.txt
```

or install it so the `sudoku-board` command is on your PATH:

```
pip install -e .
```

## Input format

A board is 81 cells, read left-to-right and top-to-bottom. `1`-`9` are
clues; `.`, `0`, or `_` are blanks. All whitespace is ignored, so both
of these are the same input:

```
53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8..79
```

```
5 3 . . 7 . . . .
6 . . 1 9 5 . . .
. 9 8 . . . . 6 .
8 . . . 6 . . . 3
4 . . 8 . 3 . . 1
7 . . . 2 . . . 6
. 6 . . . . 2 8 .
. . . 4 1 9 . . 5
. . . . 8 . . 7 9
```

## Usage

Save the puzzle above as `puzzle.txt` and run:

```
$ sudoku-board puzzle.txt
+-------+-------+-------+
| 5 3 . | . 7 . | . . . |
| 6 . . | 1 9 5 | . . . |
| . 9 8 | . . . | . 6 . |
+-------+-------+-------+
| 8 . . | . 6 . | . . 3 |
| 4 . . | 8 . 3 | . . 1 |
| 7 . . | . 2 . | . . 6 |
+-------+-------+-------+
| . 6 . | . . . | 2 8 . |
| . . . | 4 1 9 | . . 5 |
| . . . | . 8 . | . 7 9 |
+-------+-------+-------+
```

With no file argument it reads from stdin, so a puzzle can be piped in
directly. A source can also be an `http://` or `https://` URL, in which
case the puzzle text is fetched instead of read from disk:

```
$ sudoku-board https://example.com/puzzle.txt
```

Pass `--json` for a machine-readable form instead:

```
$ sudoku-board --json puzzle.txt
{
  "cells": [[5, 3, 0, 0, 7, 0, 0, 0, 0], ...],
  "valid": true,
  "conflicts": []
}
```

If two clues clash, the exit code is 1 and both output modes say why.
For example, changing the first two cells of the puzzle above to `55`
gives:

```
$ sudoku-board --json bad.txt
{
  "cells": [[5, 5, 0, 0, 7, 0, 0, 0, 0], ...],
  "valid": false,
  "conflicts": [
    {"kind": "row", "index": 0, "value": 5, "cells": [{"row": 0, "col": 0}, {"row": 0, "col": 1}]},
    {"kind": "box", "index": 0, "value": 5, "cells": [{"row": 0, "col": 0}, {"row": 0, "col": 1}]}
  ]
}
```

and the plain-text mode prints the grid followed by:

```
duplicate 5 in row 1: r1c1, r1c2
duplicate 5 in box 1: r1c1, r1c2
```

Pass `--solve` to fill in the rest of the board instead of just printing
the clues as given:

```
$ sudoku-board --solve puzzle.txt
+-------+-------+-------+
| 5 3 4 | 6 7 8 | 9 1 2 |
| 6 7 2 | 1 9 5 | 3 4 8 |
| 1 9 8 | 3 4 2 | 5 6 7 |
+-------+-------+-------+
| 8 5 9 | 7 6 1 | 4 2 3 |
| 4 2 6 | 8 5 3 | 7 9 1 |
| 7 1 3 | 9 2 4 | 8 5 6 |
+-------+-------+-------+
| 9 6 1 | 5 3 7 | 2 8 4 |
| 2 8 7 | 4 1 9 | 6 3 5 |
| 3 4 5 | 2 8 6 | 1 7 9 |
+-------+-------+-------+
```

If the clues already conflict, or if there's no way to complete the
board without breaking a rule, `--solve` exits 1 and reports why instead
of printing a board.

A board that parses fine can still be a bad puzzle - the best-known
example is having too few clues to pin down a unique solution (fewer
than 17, which is a proven lower bound). Cases like that print a
warning on stderr but otherwise proceed normally:

```
$ sudoku-board sparse.txt
warning: only 4 clues given; no 9x9 sudoku has a unique solution with fewer than 17
+-------+-------+-------+
...
```

Pass `--strict` to treat these warnings as errors instead - the board
is not printed and the command exits 1.

```
$ sudoku-board --strict sparse.txt
error: only 4 clues given; no 9x9 sudoku has a unique solution with fewer than 17
```

## Multiple files

Pass more than one path or URL to process them all in a single
invocation, in any combination. Each
board gets a `== path ==` header, and one bad file (a parse error, a
strict warning, or `--solve` finding no completion) doesn't stop the
rest from being processed - it's reported on stderr and the file's
block shows the error instead of a board:

```
$ sudoku-board puzzle.txt other.txt
== puzzle.txt ==
+-------+-------+-------+
| 5 3 . | . 7 . | . . . |
...
+-------+-------+-------+

== other.txt ==
+-------+-------+-------+
...
+-------+-------+-------+
```

The exit code is 1 if any file failed to parse or had a conflict. With
`--json`, the output is a single JSON array, one object per file, each
carrying a `"file"` key alongside the usual `cells`/`valid`/`conflicts`
fields (or just `"file"` and `"error"` for a file that couldn't be
processed).

## As a library

```python
from sudoku_board import parse, find_conflicts, parse_warnings, format_pretty, solve

board = parse(open("puzzle.txt").read())
conflicts = find_conflicts(board)
print(format_pretty(board, conflicts))

solution = solve(board)  # raises UnsolvableError if there's no completion
```

`parse` raises `BoardParseError` for structural problems (wrong cell
count, characters that aren't `1`-`9`/`.`/`0`/`_`). It never raises for
clue collisions; those come back from `find_conflicts` so you can
decide what to do with them.

`parse_warnings` returns a list of strings describing non-fatal issues
with a board that parsed successfully - right now, just having fewer
than 17 clues. It's separate from `find_conflicts` because a sparse
board isn't necessarily wrong, just suspicious.

`solve` uses plain backtracking; it returns one valid completion of the
board (there may be others if the clues don't pin down a unique
solution), or raises `UnsolvableError` if the clues conflict or no
completion exists.

## Tests

```
python -m unittest discover -s tests
```

## License

MIT, see `LICENSE`.
