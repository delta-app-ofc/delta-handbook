import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch
from scripts import validate_markdown


class MarkdownTests(unittest.TestCase):
    def validate(self, content=None, error=None, names=b"doc.md\x00"):
        output = io.StringIO()
        with patch.object(validate_markdown.subprocess, "check_output", return_value=names), patch.object(validate_markdown.Path, "read_text", return_value=content, side_effect=error), redirect_stdout(output):
            status = validate_markdown.main()
        return status, output.getvalue()

    def test_accepts_nonempty_utf8_document(self):
        status, output = self.validate("# Documento\nConteudo valido com acentos: agua.\n")
        self.assertEqual(status, 0)
        self.assertIn("1 arquivos", output)

    def test_rejects_empty_or_whitespace_document(self):
        for content in ["", " \n\t"]:
            with self.subTest(content=content):
                self.assertEqual(self.validate(content)[0], 1)

    def test_rejects_each_conflict_marker_with_line_number(self):
        for marker in ["<<<<<<< main", "=======", ">>>>>>> branch"]:
            with self.subTest(marker=marker):
                status, output = self.validate("# Titulo\n" + marker)
                self.assertEqual(status, 1)
                self.assertIn("doc.md:2:", output)

    def test_rejects_missing_file(self):
        self.assertEqual(self.validate(error=FileNotFoundError("missing"))[0], 1)

    def test_rejects_invalid_utf8(self):
        error = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid")
        self.assertEqual(self.validate(error=error)[0], 1)

    def test_handles_null_terminated_git_output_without_extra_file(self):
        self.assertEqual(self.validate("# Valido", names=b"a.md\x00b.md\x00")[0], 0)

    def test_git_failure_is_not_reported_as_valid_documents(self):
        with patch.object(validate_markdown.subprocess, "check_output", side_effect=RuntimeError("git failed")), self.assertRaises(RuntimeError):
            validate_markdown.main()
