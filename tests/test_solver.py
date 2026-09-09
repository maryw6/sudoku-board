import unittest

from sudoku_board.board import Board, parse
from sudoku_board.solver import UnsolvableError, solve

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

# A puzzle with a unique solution, equal to SOLVED above.
PUZZLE = "53..7....6..195....98....6.8...6...34..8.3..17...2...6.6....28....419..5....8.."

# Box 0 has eight distinct clues, leaving one cell that can only be 9 to
# complete the box, but 9 already appears elsewhere in that cell's row.
# No two clues clash directly, so is_valid is true, but no completion
# of the board exists.
UNSOLVABLE = (
    "123000000"
    "456000000"
    "780009000"
    + "000000000" * 6
)


class SolveTests(unittest.TestCase):
    def test_solves_a_partial_puzzle(self):
        solution = solve(parse(PUZZLE))
        self.assertEqual(solution, parse(SOLVED))

    def test_already_solved_board_is_returned_as_is(self):
        board = parse(SOLVED)
        self.assertEqual(solve(board), board)

    def test_empty_board_produces_a_complete_valid_solution(self):
        solution = solve(parse("0" * 81))
        for row in solution.cells:
            self.assertEqual(sorted(row), list(range(1, 10)))
        for i in range(9):
            self.assertEqual(sorted(solution.column(i)), list(range(1, 10)))
            self.assertEqual(sorted(solution.box(i)), list(range(1, 10)))

    def test_conflicting_clues_raise(self):
        cells = [list(row) for row in parse(SOLVED).cells]
        cells[0][1] = cells[0][0]
        with self.assertRaises(UnsolvableError):
            solve(Board(cells))

    def test_valid_but_unsolvable_clues_raise(self):
        with self.assertRaises(UnsolvableError):
            solve(parse(UNSOLVABLE))


if __name__ == "__main__":
    unittest.main()
