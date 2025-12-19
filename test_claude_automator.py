#!/usr/bin/env python3
"""Unit tests for claude_automator.py.

Tests focus on critical functionality: input validation, security boundaries,
and core logic. Run with: python -m pytest test_claude_automator.py -v
or simply: python test_claude_automator.py
"""

import tempfile
import unittest
from pathlib import Path

from claude_automator import (
    validate_path,
    validate_branch_name,
    validate_cron_expression,
    validate_positive_int,
    get_combined_prompt,
    load_northstar_prompt,
    create_default_northstar,
    IMPROVEMENT_MODES,
    NORTHSTAR_TEMPLATE,
)


class TestValidatePath(unittest.TestCase):
    """Tests for validate_path function."""

    def test_valid_existing_path(self):
        """Should return resolved Path for existing paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_path(tmpdir, must_exist=True, must_be_dir=True)
            self.assertIsInstance(result, Path)
            self.assertTrue(result.exists())
            self.assertTrue(result.is_dir())

    def test_valid_existing_file(self):
        """Should return resolved Path for existing files."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            result = validate_path(path, must_exist=True, must_be_dir=False)
            self.assertIsInstance(result, Path)
            self.assertTrue(result.exists())
        finally:
            Path(path).unlink()

    def test_nonexistent_path_raises(self):
        """Should raise ValueError for nonexistent paths when must_exist=True."""
        with self.assertRaises(ValueError) as ctx:
            validate_path("/nonexistent/path/that/does/not/exist", must_exist=True)
        self.assertIn("does not exist", str(ctx.exception))

    def test_file_when_must_be_dir_raises(self):
        """Should raise ValueError when path is file but must_be_dir=True."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            path = f.name
        try:
            with self.assertRaises(ValueError) as ctx:
                validate_path(path, must_exist=True, must_be_dir=True)
            self.assertIn("not a directory", str(ctx.exception))
        finally:
            Path(path).unlink()

    def test_nonexistent_allowed(self):
        """Should succeed for nonexistent paths when must_exist=False."""
        result = validate_path("/some/nonexistent/path", must_exist=False)
        self.assertIsInstance(result, Path)


class TestValidateBranchName(unittest.TestCase):
    """Tests for validate_branch_name function."""

    def test_valid_branch_names(self):
        """Should accept valid branch names."""
        valid_names = [
            "main",
            "feature/new-feature",
            "fix/bug-123",
            "auto-review/20231218-123456-abcd",
            "release-v1.0.0",
            "user_branch",
        ]
        for name in valid_names:
            result = validate_branch_name(name)
            self.assertEqual(result, name)

    def test_empty_branch_name_raises(self):
        """Should raise ValueError for empty branch names."""
        with self.assertRaises(ValueError) as ctx:
            validate_branch_name("")
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_whitespace_only_raises(self):
        """Should raise ValueError for whitespace-only branch names."""
        with self.assertRaises(ValueError) as ctx:
            validate_branch_name("   ")
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_shell_injection_blocked(self):
        """Should block shell metacharacters to prevent injection."""
        dangerous_inputs = [
            "branch; rm -rf /",
            "branch$(whoami)",
            "branch`id`",
            "branch|cat /etc/passwd",
            "branch&& malicious",
            "branch > /tmp/evil",
            "branch < /etc/shadow",
            "branch\nmalicious",
            "branch\rmalicious",
            "branch\0malicious",
        ]
        for name in dangerous_inputs:
            with self.assertRaises(ValueError) as ctx:
                validate_branch_name(name)
            self.assertIn("invalid character", str(ctx.exception))

    def test_invalid_git_ref_names(self):
        """Should reject invalid git ref name patterns."""
        invalid_names = [
            "-starts-with-dash",
            ".starts-with-dot",
            "contains..double-dots",
            "ends-with.lock",
            "ends-with-slash/",
        ]
        for name in invalid_names:
            with self.assertRaises(ValueError):
                validate_branch_name(name)

    def test_too_long_branch_name_raises(self):
        """Should reject branch names over 250 characters."""
        long_name = "x" * 251
        with self.assertRaises(ValueError) as ctx:
            validate_branch_name(long_name)
        self.assertIn("too long", str(ctx.exception))


class TestValidateCronExpression(unittest.TestCase):
    """Tests for validate_cron_expression function."""

    def test_valid_cron_expressions(self):
        """Should accept valid cron expressions."""
        valid_exprs = [
            "* * * * *",
            "0 * * * *",
            "0 0 * * *",
            "0 0 1 * *",
            "0 0 * * 0",
            "*/15 * * * *",
            "0 9-17 * * 1-5",
        ]
        for expr in valid_exprs:
            result = validate_cron_expression(expr)
            self.assertEqual(result, expr)

    def test_empty_expression_raises(self):
        """Should raise ValueError for empty expressions."""
        with self.assertRaises(ValueError) as ctx:
            validate_cron_expression("")
        self.assertIn("cannot be empty", str(ctx.exception))

    def test_wrong_field_count_raises(self):
        """Should raise ValueError for wrong number of fields."""
        invalid_exprs = [
            "* * * *",      # 4 fields
            "* * * * * *",  # 6 fields
            "0 0",          # 2 fields
        ]
        for expr in invalid_exprs:
            with self.assertRaises(ValueError) as ctx:
                validate_cron_expression(expr)
            self.assertIn("5 fields", str(ctx.exception))

    def test_shell_injection_blocked(self):
        """Should block shell metacharacters."""
        dangerous_inputs = [
            "* * * * *; rm -rf /",
            "* * * * * && cat /etc/passwd",
            "$(whoami) * * * *",
        ]
        for expr in dangerous_inputs:
            with self.assertRaises(ValueError) as ctx:
                validate_cron_expression(expr)
            self.assertIn("invalid character", str(ctx.exception))


class TestValidatePositiveInt(unittest.TestCase):
    """Tests for validate_positive_int function."""

    def test_valid_positive_integers(self):
        """Should accept positive integers."""
        self.assertEqual(validate_positive_int(1, "test"), 1)
        self.assertEqual(validate_positive_int(100, "test"), 100)
        self.assertEqual(validate_positive_int(1000000, "test"), 1000000)

    def test_zero_raises(self):
        """Should raise ValueError for zero."""
        with self.assertRaises(ValueError) as ctx:
            validate_positive_int(0, "count")
        self.assertIn("positive integer", str(ctx.exception))

    def test_negative_raises(self):
        """Should raise ValueError for negative integers."""
        with self.assertRaises(ValueError) as ctx:
            validate_positive_int(-5, "iterations")
        self.assertIn("positive integer", str(ctx.exception))

    def test_max_value_enforced(self):
        """Should raise ValueError when value exceeds max_value."""
        with self.assertRaises(ValueError) as ctx:
            validate_positive_int(100, "interval", max_value=60)
        self.assertIn("cannot exceed", str(ctx.exception))

    def test_at_max_value_allowed(self):
        """Should accept value equal to max_value."""
        result = validate_positive_int(60, "interval", max_value=60)
        self.assertEqual(result, 60)


class TestGetCombinedPrompt(unittest.TestCase):
    """Tests for get_combined_prompt function."""

    def test_single_mode(self):
        """Should return the mode's prompt for single mode."""
        result = get_combined_prompt(["fix_bugs"])
        self.assertEqual(result, IMPROVEMENT_MODES["fix_bugs"]["prompt"])

    def test_multiple_modes(self):
        """Should combine prompts for multiple modes."""
        result = get_combined_prompt(["fix_bugs", "security"])
        self.assertIn("Fix Bugs", result)
        self.assertIn("Security Review", result)
        self.assertIn("multiple types of code improvements", result)

    def test_all_modes_have_required_fields(self):
        """Should verify all modes have required fields."""
        for key, mode in IMPROVEMENT_MODES.items():
            self.assertIn("name", mode, f"Mode {key} missing 'name'")
            self.assertIn("description", mode, f"Mode {key} missing 'description'")
            self.assertIn("prompt", mode, f"Mode {key} missing 'prompt'")


class TestNorthstarFunctions(unittest.TestCase):
    """Tests for NORTHSTAR.md related functions."""

    def test_create_default_northstar_success(self):
        """Should create NORTHSTAR.md successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            success, msg = create_default_northstar(project_dir)
            self.assertTrue(success)
            self.assertTrue((project_dir / "NORTHSTAR.md").exists())

    def test_create_default_northstar_already_exists(self):
        """Should fail if NORTHSTAR.md already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "NORTHSTAR.md").write_text("existing content")
            success, msg = create_default_northstar(project_dir)
            self.assertFalse(success)
            self.assertIn("already exists", msg)

    def test_load_northstar_prompt_success(self):
        """Should load and format NORTHSTAR.md content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "NORTHSTAR.md").write_text("# Test North Star\n\nVision here")
            prompt, error = load_northstar_prompt(project_dir)
            self.assertIsNotNone(prompt)
            self.assertIsNone(error)
            self.assertIn("Test North Star", prompt)

    def test_load_northstar_prompt_not_found(self):
        """Should return error if NORTHSTAR.md not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            prompt, error = load_northstar_prompt(project_dir)
            self.assertIsNone(prompt)
            self.assertIn("not found", error)

    def test_load_northstar_prompt_empty_file(self):
        """Should return error if NORTHSTAR.md is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            (project_dir / "NORTHSTAR.md").write_text("")
            prompt, error = load_northstar_prompt(project_dir)
            self.assertIsNone(prompt)
            self.assertIn("empty", error)


if __name__ == "__main__":
    unittest.main()
