import os
import unittest
from unittest.mock import patch

from ai_git_helper import GitSnapshot, build_messages, limit_diff, mask_sensitive, main, parse_commit, parse_pr


class AiGitHelperTest(unittest.TestCase):
    def test_safe_mode_and_output_normalization(self):
        masked = mask_sensitive("email=dev@example.com token=sk-12345678901234567890")
        self.assertNotIn("dev@example.com", masked)
        self.assertNotIn("sk-12345678901234567890", masked)
        self.assertIn("SAFE MODE", limit_diff("\n".join(f"line {i}" for i in range(5)), 1, 2))

        title, body = parse_commit("COMMIT_TITLE: fix: parser\nCOMMIT_BODY:\n- reject empty input")
        self.assertEqual(title, "fix: parser")
        self.assertEqual(body, "- reject empty input")

    def test_pr_sections_are_guaranteed(self):
        snapshot = GitSnapshot(" M main.py", "diff", "main")
        title, body = parse_pr("PR_TITLE: fix parser\nPR_BODY:\n## What\n- update parser", snapshot)
        self.assertEqual(title, "fix parser")
        for section in ("## Why", "## What", "## How to Test"):
            self.assertIn(section, body)

    def test_prompt_contains_diff_and_safe_limit(self):
        snapshot = GitSnapshot(" M main.py", "email=dev@example.com\n" + "x\n" * 5, "main")
        prompt = build_messages("commit", snapshot, True, 1, 2)[1]["content"]
        self.assertNotIn("dev@example.com", prompt)
        self.assertIn("SAFE MODE", prompt)

    def test_no_changes_does_not_call_api(self):
        with patch("ai_git_helper.collect_snapshot", return_value=GitSnapshot("", "", "main")), patch(
            "ai_git_helper.call_ai"
        ) as call:
            self.assertEqual(main(["commit"]), 0)
            call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
