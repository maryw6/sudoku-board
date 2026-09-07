import unittest

from sudoku_board.board import (
    Board,
    BoardParseError,
    Conflict,
    find_conflicts,
    is_valid,
    parse,
)

# A complete, valid solution. Used as a base for conflict tests since any
# single edit to it is guaranteed to introduce exactly the conflict we want.
SOLVED = (
    "534678912"
    "672195348"
    "198342567"
    "859761423"
    "426853791"
    "713924856"
    "961537284"
    "287419635"
    "345286179"
)


class ParseTests(unittest.TestCase):
    def test_single_line(self):
        text = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8.."
        board = parse(text)
        self.assertEqual(board.cells[0], [5, 3, 0, 0, 7, 0, 0, 0, 0])
        self.assertEqual(board.cells[8], [0, 0, 0, 0, 8, 0, 0, 7, 9])

    def test_multiline_grid_matches_single_line(self):
        single = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8.."
        grid = "\n".join(
            " ".join(single[r * 9:(r + 1) * 9]) for r in range(9)
        )
        self.assertEqual(parse(single), parse(grid))

    def test_underscore_and_zero_both_mean_empty(self):
        text = ("1" + "_" * 8) * 9
        board_underscore = parse(text)
        board_zero = parse(text.replace("_", "0"))
        self.assertEqual(board_underscore, board_zero)

    def test_wrong_length_raises(self):
        with self.assertRaises(BoardParseError):
            parse("123")

    def test_invalid_character_raises(self):
        with self.assertRaises(BoardParseError):
            parse(SOLVED[:40] + "x" + SOLVED[41:])

    def test_whitespace_is_ignored(self):
        text = "\n\t ".join(SOLVED)
        self.assertEqual(parse(text), parse(SOLVED))


class BoardUnitTests(unittest.TestCase):
    def setUp(self):
        self.board = parse(SOLVED)

    def test_row(self):
        self.assertEqual(self.board.row(0), [5, 3, 4, 6, 7, 8, 9, 1, 2])

    def test_column(self):
        self.assertEqual(self.board.column(0), [5, 6, 1, 8, 4, 7, 9, 2, 3])

    def test_box(self):
        self.assertEqual(self.board.box(0), [5, 3, 4, 6, 7, 2, 1, 9, 8])


class FindConflictsTests(unittest.TestCase):
    def test_solved_board_has_no_conflicts(self):
        board = parse(SOLVED)
        self.assertEqual(find_conflicts(board), [])
        self.assertTrue(is_valid(board))

    def test_empty_board_has_no_conflicts(self):
        board = parse("0" * 81)
        self.assertEqual(find_conflicts(board), [])
        self.assertTrue(is_valid(board))

    def test_row_conflict(self):
        cells = [list(row) for row in parse(SOLVED).cells]
        cells[0][1] = cells[0][0]  # duplicate the first cell's value
        board = Board(cells)
        conflicts = find_conflicts(board)
        self.assertIn(
            Conflict("row", 0, cells[0][0], ((0, 0), (0, 1))), conflicts
        )
        self.assertFalse(is_valid(board))

    def test_column_conflict(self):
        cells = [list(row) for row in parse(SOLVED).cells]
        cells[1][0] = cells[0][0]  # duplicate down column 0
        board = Board(cells)
        conflicts = find_conflicts(board)
        self.assertIn(
            Conflict("column", 0, cells[0][0], ((0, 0), (1, 0))), conflicts
        )

    def test_box_conflict(self):
        cells = [list(row) for row in parse(SOLVED).cells]
        cells[1][1] = cells[0][0]  # same top-left box, distinct row/column
        board = Board(cells)
        conflicts = find_conflicts(board)
        kinds = {c.kind for c in conflicts}
        self.assertIn("box", kinds)

    def test_multiple_equal_values_report_every_pair_once(self):
        cells = [list(row) for row in parse(SOLVED).cells]
        cells[0][1] = cells[0][0]
        cells[0][2] = cells[0][0]
        board = Board(cells)
        row_conflicts = [c for c in find_conflicts(board) if c.kind == "row"]
        self.assertEqual(len(row_conflicts), 1)
        self.assertEqual(row_conflicts[0].cells, ((0, 0), (0, 1), (0, 2)))


if __name__ == "__main__":
    unittest.main()
