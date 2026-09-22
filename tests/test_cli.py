import contextlib
import io
import json
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from sudoku_board.cli import main

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

# First two cells duplicated: a row (and box) conflict.
CONFLICTING = "55" + SOLVED[2:]

# Too short to parse at all.
MALFORMED = "123"


def _run(argv, stdin_text=None):
    stdin = io.StringIO(stdin_text or "")
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        with unittest.mock.patch("sys.stdin", stdin):
            code = main(argv)
    return code, out.getvalue(), err.getvalue()


class SingleSourceTests(unittest.TestCase):
    def test_stdin_default_has_no_header(self):
        code, out, _ = _run([], stdin_text=SOLVED)
        self.assertEqual(code, 0)
        self.assertNotIn("==", out)
        self.assertIn("| 5 3 4 | 6 7 8 | 9 1 2 |", out)

    def test_single_file_has_no_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "puzzle.txt")
            path.write_text(SOLVED)
            code, out, _ = _run([str(path)])
        self.assertEqual(code, 0)
        self.assertNotIn(f"== {path} ==", out)

    def test_single_file_conflict_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "bad.txt")
            path.write_text(CONFLICTING)
            code, out, _ = _run([str(path)])
        self.assertEqual(code, 1)
        self.assertIn("duplicate", out)


class MultipleFileTests(unittest.TestCase):
    def _write(self, tmp, name, text):
        path = Path(tmp, name)
        path.write_text(text)
        return str(path)

    def test_each_file_gets_a_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self._write(tmp, "a.txt", SOLVED)
            b = self._write(tmp, "b.txt", SOLVED)
            code, out, _ = _run([a, b])
        self.assertEqual(code, 0)
        self.assertIn(f"== {a} ==", out)
        self.assertIn(f"== {b} ==", out)

    def test_one_bad_file_does_not_block_the_others(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = self._write(tmp, "good.txt", SOLVED)
            bad = self._write(tmp, "bad.txt", MALFORMED)
            code, out, err = _run([good, bad])
        self.assertEqual(code, 1)
        self.assertIn(f"== {good} ==", out)
        self.assertIn("| 5 3 4 | 6 7 8 | 9 1 2 |", out)
        self.assertIn(f"error: {bad}:", err)

    def test_json_mode_produces_an_array_with_file_names(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = self._write(tmp, "a.txt", SOLVED)
            b = self._write(tmp, "b.txt", CONFLICTING)
            code, out, _ = _run(["--json", a, b])
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload[0]["file"], a)
        self.assertTrue(payload[0]["valid"])
        self.assertEqual(payload[1]["file"], b)
        self.assertFalse(payload[1]["valid"])

    def test_json_mode_reports_parse_errors_inline(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = self._write(tmp, "good.txt", SOLVED)
            bad = self._write(tmp, "bad.txt", MALFORMED)
            code, out, _ = _run(["--json", good, bad])
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertNotIn("error", payload[0])
        self.assertIn("error", payload[1])
        self.assertEqual(payload[1]["file"], bad)

    def test_strict_fails_only_the_sparse_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            full = self._write(tmp, "full.txt", SOLVED)
            sparse = self._write(tmp, "sparse.txt", "0" * 81)
            code, out, err = _run(["--strict", full, sparse])
        self.assertEqual(code, 1)
        self.assertIn(f"== {full} ==", out)
        self.assertIn(f"== {sparse} ==\nerror:", out)
        self.assertIn(f"error: {sparse}:", err)


if __name__ == "__main__":
    unittest.main()
