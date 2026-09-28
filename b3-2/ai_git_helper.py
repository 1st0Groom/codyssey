"""Git 변경 사항으로 커밋 메시지와 PR 초안을 만드는 CLI."""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class GitSnapshot:
    status: str
    diff: str
    branch: str


def run_git(*args):
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} 실패: {detail}")
    return result.stdout


def collect_snapshot():
    status = run_git("status", "--short", "--untracked-files=all", "--", ".")
    branch = run_git("branch", "--show-current").strip() or "detached HEAD"
    has_head = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        capture_output=True,
    ).returncode == 0
    if has_head:
        diff = run_git("diff", "--no-ext-diff", "--unified=3", "HEAD", "--", ".")
    else:
        diff = run_git("diff", "--no-ext-diff", "--unified=3", "--", ".")
        diff += run_git("diff", "--cached", "--no-ext-diff", "--unified=3", "--", ".")
    return GitSnapshot(status=status, diff=diff, branch=branch)


def mask_sensitive(text):
    """safe mode에서 흔한 토큰·이메일·비밀값을 마스킹한다."""
    text = re.sub(
        r"-----BEGIN [^-]+ PRIVATE KEY-----.*?-----END [^-]+ PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16})\b",
        "[REDACTED_TOKEN]",
        text,
    )
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    text = re.sub(
        r"(?i)(api[_-]?key|secret|token|password)(\s*[:=]\s*)[^\s,\"']+",
        r"\1\2[REDACTED]",
        text,
    )
    return re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._-]+", r"\1[REDACTED_TOKEN]", text)


def limit_diff(diff, max_files, max_lines):
    lines = diff.splitlines()
    selected = []
    file_count = 0
    truncated = False
    for line in lines:
        if line.startswith("diff --git "):
            if file_count >= max_files:
                truncated = True
                break
            file_count += 1
        if len(selected) >= max_lines:
            truncated = True
            break
        selected.append(line)
    if len(selected) < len(lines):
        truncated = True
    if truncated:
        selected.append(
            f"[SAFE MODE: diff를 최대 {max_files}개 파일, {max_lines}줄로 제한했습니다]"
        )
    return "\n".join(selected)


def prepare_diff(diff, safe_mode, max_files, max_lines):
    if not safe_mode:
        return diff
    return limit_diff(mask_sensitive(diff), max_files, max_lines)


def build_messages(command, snapshot, safe_mode, max_files, max_lines):
    diff = prepare_diff(snapshot.diff, safe_mode, max_files, max_lines)
    output_format = (
        "COMMIT_TITLE: 한 줄 제목\nCOMMIT_BODY:\n- 선택적 본문 불릿"
        if command == "commit"
        else "PR_TITLE: 한 줄 제목\nPR_BODY:\n## Why\n- 불릿\n\n## What\n- 불릿\n\n## How to Test\n- 불릿"
    )
    instruction = (
        "Git status와 diff만 근거로 작성하세요. 없는 사실, 테스트 결과, 수치, 파일 변경을 만들지 마세요. "
        "지정한 형식만 반환하고 마크다운 코드 펜스는 사용하지 마세요."
    )
    if command == "commit":
        instruction += " 커밋 제목은 명령형 한 줄, 최대 72자로 작성하세요. 본문은 필요할 때만 1~3개 불릿으로 작성하세요."
    else:
        instruction += " PR 제목은 최대 80자이며 Why, What, How to Test 각 섹션에 최소 1개 불릿을 넣으세요."
    user_content = (
        f"{instruction}\n\n현재 브랜치: {snapshot.branch}\n"
        f"git status --short:\n{snapshot.status.strip() or '(변경 없음)'}\n\n"
        f"git diff:\n{diff or '(diff 없음; 상태 목록을 기준으로 작성)'}\n\n"
        f"출력 형식:\n{output_format}"
    )
    return [
        {"role": "system", "content": "당신은 변경 내용을 보수적으로 요약하는 Git 도우미입니다."},
        {"role": "user", "content": user_content},
    ]


def call_ai(messages, api_key, api_url, model, temperature, max_tokens, timeout):
    payload_data = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if not re.match(r"^(?:gpt-5|o[1-9])", model.lower()):
        payload_data["temperature"] = temperature
    payload = json.dumps(payload_data).encode("utf-8")
    request = urllib.request.Request(
        api_url,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"AI API HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"AI API 네트워크 오류: {error.reason}") from error
    except TimeoutError as error:
        raise RuntimeError("AI API 요청 시간이 초과되었습니다") from error
    except json.JSONDecodeError as error:
        raise RuntimeError("AI API 응답을 JSON으로 해석하지 못했습니다") from error

    try:
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "\n".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        content = str(content).strip()
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("AI API 응답 형식이 예상과 다릅니다") from error
    if not content:
        raise RuntimeError("AI API 응답에 생성된 내용이 없습니다")
    return content


def clean_generated_text(text):
    return re.sub(r"```(?:text|markdown)?\s*|```", "", text, flags=re.IGNORECASE).strip()


def parse_commit(text):
    lines = clean_generated_text(text).splitlines()
    title_index = next(
        (i for i, line in enumerate(lines) if line.strip().upper().startswith("COMMIT_TITLE:")),
        None,
    )
    if title_index is not None:
        title = lines[title_index].split(":", 1)[1].strip()
        body_start = next(
            (i + 1 for i in range(title_index + 1, len(lines)) if lines[i].strip().upper() == "COMMIT_BODY:"),
            len(lines),
        )
        body = "\n".join(lines[body_start:]).strip()
    else:
        nonempty = [(i, line.strip()) for i, line in enumerate(lines) if line.strip()]
        if not nonempty:
            raise ValueError("커밋 제목이 비어 있습니다")
        title_index, title = nonempty[0]
        body = "\n".join(lines[title_index + 1:]).strip()
    title = re.sub(r"^#+\s*", "", title)
    title = re.sub(r"^(?:title|commit message)\s*:\s*", "", title, flags=re.IGNORECASE)
    title = " ".join(title.split())[:72].rstrip()
    if not title:
        raise ValueError("커밋 제목이 비어 있습니다")
    body_lines = [line.strip() for line in body.splitlines() if line.strip()]
    if body_lines and not any(line.startswith("-") for line in body_lines):
        body = "\n".join(f"- {line}" for line in body_lines)
    return title, body


def section_body(body, name, fallback):
    pattern = rf"(?ims)^##\s*{re.escape(name)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
    match = re.search(pattern, body)
    content_lines = [line.strip() for line in (match.group(1).strip() if match else "").splitlines() if line.strip()]
    if not any(line.startswith("-") for line in content_lines):
        content_lines.insert(0, f"- {fallback}")
    return "\n".join(content_lines)


def parse_pr(text, snapshot):
    clean = clean_generated_text(text)
    lines = clean.splitlines()
    title_index = next(
        (i for i, line in enumerate(lines) if line.strip().upper().startswith("PR_TITLE:")),
        None,
    )
    if title_index is not None:
        title = lines[title_index].split(":", 1)[1].strip()
        body_start = next(
            (i + 1 for i in range(title_index + 1, len(lines)) if lines[i].strip().upper() == "PR_BODY:"),
            title_index + 1,
        )
        body = "\n".join(lines[body_start:]).strip()
    else:
        title = next((line.strip() for line in lines if line.strip() and not line.startswith("##")), "")
        body = clean[clean.find("## Why"):] if "## Why" in clean else clean
    title = re.sub(r"^#+\s*", "", title)
    title = re.sub(r"^(?:title|pr title)\s*:\s*", "", title, flags=re.IGNORECASE)
    title = " ".join(title.split())[:80].rstrip() or "chore: summarize current changes"
    changed = ", ".join(line[3:].strip() for line in snapshot.status.splitlines()[:3])
    what_fallback = "변경 파일과 diff의 핵심 내용을 반영했습니다"
    if changed:
        what_fallback += f" ({changed})"
    return title, (
        "## Why\n"
        + section_body(body, "Why", "현재 변경 사항을 일관된 PR 형식으로 검토하기 위해 작성했습니다.")
        + "\n\n## What\n"
        + section_body(body, "What", what_fallback + ".")
        + "\n\n## How to Test\n"
        + section_body(body, "How to Test", "변경 diff를 확인하고 프로젝트 테스트를 실행합니다.")
    )


def positive_int(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("0보다 큰 정수를 입력하세요")
    return number


def temperature(value):
    number = float(value)
    if not 0 <= number <= 2:
        raise argparse.ArgumentTypeError("temperature는 0~2 범위여야 합니다")
    return number


def add_options(parser, suppress_defaults=False):
    def default(value):
        return argparse.SUPPRESS if suppress_defaults else value

    parser.add_argument("--model", "-model", default=default(None))
    parser.add_argument("--temperature", "-temperature", type=temperature, default=default(None))
    parser.add_argument("--max-tokens", "-max-tokens", type=positive_int, default=default(None))
    parser.add_argument("--api-url", default=default(None))
    parser.add_argument("--timeout", type=positive_int, default=default(None))
    parser.add_argument("--max-files", type=positive_int, default=default(None))
    parser.add_argument("--max-lines", type=positive_int, default=default(None))
    safe = parser.add_mutually_exclusive_group()
    safe.add_argument("--safe-mode", "-safe-mode", dest="safe_mode", action="store_true", default=default(None))
    safe.add_argument("--no-safe-mode", dest="safe_mode", action="store_false", default=default(None))


def build_parser():
    parser = argparse.ArgumentParser(description="Git 변경 사항으로 AI 커밋/PR 초안을 생성합니다.")
    add_options(parser)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("commit", "pr"):
        command_parser = commands.add_parser(command, help=f"{command} 초안 생성")
        add_options(command_parser, suppress_defaults=True)
    return parser


def env_value(*names):
    return next((os.getenv(name, "").strip() for name in names if os.getenv(name, "").strip()), "")


def load_dotenv():
    env_path = Path(__file__).with_name(".env")
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        name, separator, value = line.partition("=")
        if separator and name.strip() and name.strip() not in os.environ:
            os.environ[name.strip()] = value.strip().strip("\"'")


def resolve_options(args):
    api_url = args.api_url or env_value("NAITO_API_URL", "AI_API_URL", "OPENAI_BASE_URL")
    api_key = env_value("NAITO_API_KEY", "AI_API_KEY")
    if not api_key and "openrouter.ai" in api_url:
        api_key = env_value("OPENROUTER_API_KEY")
    return {
        "api_url": api_url,
        "api_key": api_key,
        "model": args.model or env_value("NAITO_MODEL", "AI_MODEL") or DEFAULT_MODEL,
        "temperature": 0.2 if args.temperature is None else args.temperature,
        "max_tokens": 2000 if args.max_tokens is None else args.max_tokens,
        "timeout": 60 if args.timeout is None else args.timeout,
        "max_files": 10 if args.max_files is None else args.max_files,
        "max_lines": 200 if args.max_lines is None else args.max_lines,
        "safe_mode": bool(args.safe_mode),
    }


def main(argv=None):
    load_dotenv()
    args = build_parser().parse_args(argv)
    options = resolve_options(args)
    try:
        snapshot = collect_snapshot()
    except (OSError, RuntimeError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    changed_files = [line for line in snapshot.status.splitlines() if line.strip()]
    if not changed_files:
        print("[INFO] 변경 사항이 없습니다. 초안을 생성하지 않고 종료합니다.")
        return 0

    print(f"[INFO] Git status 수집 완료: {len(changed_files)}개 파일 변경 감지")
    print(f"[INFO] Git diff 수집 완료: {len(snapshot.diff.splitlines())}줄")
    if not options["api_key"]:
        print(
            "[ERROR] NAITO_API_KEY 환경변수가 설정되지 않았습니다. "
            '예: export NAITO_API_KEY="YOUR_KEY"',
            file=sys.stderr,
        )
        return 1
    if not options["api_url"]:
        print(
            "[ERROR] NAITO_API_URL 환경변수가 설정되지 않았습니다. "
            '네이토가 안내한 Chat Completions 주소를 .env에 입력하세요.',
            file=sys.stderr,
        )
        return 1

    print("[INFO] Naito AI API 요청 중... (1회)")
    try:
        generated = call_ai(
            build_messages(
                args.command,
                snapshot,
                options["safe_mode"],
                options["max_files"],
                options["max_lines"],
            ),
            options["api_key"],
            options["api_url"],
            options["model"],
            options["temperature"],
            options["max_tokens"],
            options["timeout"],
        )
        if args.command == "commit":
            title, body = parse_commit(generated)
            print("[DONE] 커밋 메시지 생성 완료\n\n--- Commit Message ---")
            print(title)
            if body:
                print(f"\n{body}")
        else:
            title, body = parse_pr(generated, snapshot)
            print(f"[INFO] 현재 브랜치: {snapshot.branch}")
            print("[DONE] PR 초안 생성 완료\n\n--- PR Title ---")
            print(title)
            print(f"\n--- PR Body ---\n{body}")
        print("\n----------------------")
        return 0
    except (RuntimeError, ValueError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
