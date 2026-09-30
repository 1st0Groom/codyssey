import os
import unittest
from io import StringIO
from unittest.mock import patch

from ai_git_helper import (
    GitSnapshot,
    build_messages,
    interactive_cli,
    limit_diff,
    main,
    mask_sensitive,
    parse_commit,
    parse_pr,
)


class AiGitHelperTest(unittest.TestCase):
    def test_safe_mode_and_output_normalization(self):
        # 민감정보를 가리고, AI 답변 형식을 정리하는지 확인함.
        masked = mask_sensitive("email=dev@example.com token=sk-12345678901234567890")
        self.assertNotIn("dev@example.com", masked)
        self.assertNotIn("sk-12345678901234567890", masked)
        self.assertIn("SAFE MODE", limit_diff("\n".join(f"line {i}" for i in range(5)), 1, 2))

        title, body = parse_commit("COMMIT_TITLE: fix: parser\nCOMMIT_BODY:\n- reject empty input")
        self.assertEqual(title, "fix: parser")
        self.assertEqual(body, "- reject empty input")

    def test_pr_sections_are_guaranteed(self):
        # AI가 일부 섹션을 빼먹어도 PR 구조를 채우는지 확인함.
        snapshot = GitSnapshot(" M main.py", "diff", "main")
        title, body = parse_pr("PR_TITLE: fix parser\nPR_BODY:\n## What\n- update parser", snapshot)
        self.assertEqual(title, "fix parser")
        for section in ("## Why", "## What", "## How to Test"):
            self.assertIn(section, body)

    def test_prompt_contains_diff_and_safe_limit(self):
        # safe mode가 실제 프롬프트에도 적용되는지 확인함.
        snapshot = GitSnapshot(" M main.py", "email=dev@example.com\n" + "x\n" * 5, "main")
        prompt = build_messages("commit", snapshot, True, 1, 2)[1]["content"]
        self.assertNotIn("dev@example.com", prompt)
        self.assertIn("SAFE MODE", prompt)

    def test_no_changes_does_not_call_api(self):
        # 바뀐 게 없으면 API를 호출하지 않는 게 맞음.
        with patch("ai_git_helper.collect_snapshot", return_value=GitSnapshot("", "", "main")), patch(
            "ai_git_helper.call_ai"
        ) as call:
            self.assertEqual(main(["commit"]), 0)
            call.assert_not_called()

    def test_interactive_cli_accepts_multiple_commands(self):
        # CLI를 한 번 켠 뒤 commit/pr을 연달아 받을 수 있는지 확인함.
        with patch("builtins.input", side_effect=["help", "commit", "pr", "exit"]), patch(
            "ai_git_helper.collect_snapshot", return_value=GitSnapshot("", "", "main")
        ), patch("ai_git_helper.call_ai") as call, patch("sys.stdout", new_callable=StringIO) as output:
            self.assertEqual(interactive_cli(), 0)
            self.assertIn("commit [옵션]", output.getvalue())
            call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
