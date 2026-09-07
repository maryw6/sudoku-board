import json
import unittest

from sudoku_board.board import Board, Conflict, parse
from sudoku_board.printer import format_json, format_pretty

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


class FormatPrettyTests(unittest.TestCase):
    def test_layout_of_a_clean_board(self):
        board = parse("." * 81)
        text = format_pretty(board)
        lines = text.splitlines()
        self.assertEqual(len(lines), 13)  # 4 separators + 9 rows
        self.assertEqual(lines[0], "+-------+-------+-------+")
        self.assertEqual(lines[1], "| . . . | . . . | . . . |")

    def test_digits_appear_in_the_grid(self):
        board = parse(SOLVED)
        text = format_pretty(board)
        self.assertIn("| 5 3 4 | 6 7 8 | 9 1 2 |", text)

    def test_no_conflict_section_when_valid(self):
        board = parse(SOLVED)
        text = format_pretty(board)
        self.assertNotIn("duplicate", text)

    def test_conflicts_are_listed_after_the_grid(self):
        cells = [list(row) for row in parse(SOLVED).cells]
        cells[0][1] = cells[0][0]
        board = Board(cells)
        text = format_pretty(board)
        self.assertIn("duplicate 5 in row 1: r1c1, r1c2", text)

    def test_precomputed_conflicts_are_reused_not_recomputed(self):
        board = parse(SOLVED)
        fake_conflict = Conflict("row", 3, 7, ((3, 0), (3, 1)))
        text = format_pretty(board, conflicts=[fake_conflict])
        self.assertIn("duplicate 7 in row 4: r4c1, r4c2", text)


class FormatJsonTests(unittest.TestCase):
    def test_valid_board_round_trips(self):
        board = parse(SOLVED)
        payload = json.loads(format_json(board))
        self.assertEqual(payload["cells"], board.cells)
        self.assertTrue(payload["valid"])
        self.assertEqual(payload["conflicts"], [])

    def test_conflict_shape(self):
        cells = [list(row) for row in parse(SOLVED).cells]
        cells[0][1] = cells[0][0]
        board = Board(cells)
        payload = json.loads(format_json(board))
        self.assertFalse(payload["valid"])
        row_conflicts = [c for c in payload["conflicts"] if c["kind"] == "row"]
        self.assertEqual(len(row_conflicts), 1)
        self.assertEqual(row_conflicts[0]["value"], cells[0][0])
        self.assertEqual(
            row_conflicts[0]["cells"],
            [{"row": 0, "col": 0}, {"row": 0, "col": 1}],
        )

    def test_precomputed_conflicts_are_reused_not_recomputed(self):
        board = parse(SOLVED)
        fake_conflict = Conflict("box", 2, 9, ((0, 6), (0, 7)))
        payload = json.loads(format_json(board, conflicts=[fake_conflict]))
        self.assertFalse(payload["valid"])
        self.assertEqual(len(payload["conflicts"]), 1)
        self.assertEqual(payload["conflicts"][0]["kind"], "box")


if __name__ == "__main__":
    unittest.main()
