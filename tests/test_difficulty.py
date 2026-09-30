import unittest
import unittest.mock

from sudoku_board.board import Board, parse
from sudoku_board.difficulty import LEVELS, estimate_difficulty
from sudoku_board.solver import UnsolvableError

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

PUZZLE = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8.."

# Valid clues, but box 0's last open cell can only be 9 and its row
# already has one.
UNSOLVABLE = (
    "123000000"
    "456000000"
    "780009000"
    + "000000000" * 6
)


class EstimateDifficultyTests(unittest.TestCase):
    def test_solved_board_is_easy(self):
        result = estimate_difficulty(parse(SOLVED))
        self.assertEqual(result.level, "easy")
        self.assertEqual(result.technique, "naked singles")
        self.assertEqual(result.clues, 81)

    def test_one_blank_cell_is_a_naked_single(self):
        cells = [list(row) for row in parse(SOLVED).cells]
        cells[4][4] = 0
        result = estimate_difficulty(Board(cells))
        self.assertEqual(result.level, "easy")
        self.assertEqual(result.clues, 80)

    def test_empty_board_needs_backtracking(self):
        result = estimate_difficulty(parse("0" * 81))
        self.assertEqual(result.level, "hard")
        self.assertEqual(result.technique, "backtracking")
        self.assertEqual(result.clues, 0)

    def test_classic_puzzle_yields_to_singles(self):
        result = estimate_difficulty(parse(PUZZLE))
        self.assertIn(result.level, LEVELS)
        self.assertNotEqual(result.level, "hard")
        self.assertEqual(result.clues, 30)

    def test_few_clues_bump_a_singles_only_board_up_a_step(self):
        with unittest.mock.patch("sudoku_board.difficulty.FEW_CLUES", 82):
            result = estimate_difficulty(parse(SOLVED))
        self.assertEqual(result.level, "medium")
        self.assertEqual(result.technique, "naked singles")

    def test_conflicting_clues_raise(self):
        cells = [list(row) for row in parse(SOLVED).cells]
        cells[0][1] = cells[0][0]
        with self.assertRaises(UnsolvableError):
            estimate_difficulty(Board(cells))

    def test_valid_but_unsolvable_clues_raise(self):
        with self.assertRaises(UnsolvableError):
            estimate_difficulty(parse(UNSOLVABLE))


if __name__ == "__main__":
    unittest.main()
