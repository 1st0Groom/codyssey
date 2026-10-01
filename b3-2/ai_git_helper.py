"""Git 변경 사항으로 커밋 메시지와 PR 초안을 만드는 CLI."""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


# .env에 모델을 안 적었을 때만 쓰는 기본값임. 지금은 .env에서 gpt-5-mini를 씀.
DEFAULT_MODEL = "gpt-4o-mini"


@dataclass
class GitSnapshot:
    # AI한테 보내기 전에 현재 Git 상태를 이 묶음으로 정리해 둠.
    status: str
    diff: str
    branch: str


def run_git(*args):
    # 파이썬에서 git 명령어를 대신 실행하는 공통 함수임.
    # 여기서 실패를 잡아야 아래 함수들이 복잡해지지 않음.
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode:
        # git이 실패했으면 조용히 넘어가지 말고 원인을 보여줌.
        detail = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} 실패: {detail}")
    return result.stdout


def collect_snapshot():
    # 현재 폴더 아래에서 바뀐 파일 목록을 먼저 가져옴.
    # diff만 보면 새 파일 내용이 빠질 수 있어서 status도 같이 보는 거임.
    status = run_git("status", "--short", "--untracked-files=all", "--", ".")
    branch = run_git("branch", "--show-current").strip() or "detached HEAD"
    # 아직 첫 커밋도 없는 저장소에서는 HEAD 기준 diff가 안 되니까 따로 처리함.
    has_head = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        capture_output=True,
    ).returncode == 0
    if has_head:
        # HEAD와 현재 작업 폴더의 차이를 가져옴. 범위는 현재 폴더로 한정.
        diff = run_git("diff", "--no-ext-diff", "--unified=3", "HEAD", "--", ".")
    else:
        # 첫 커밋 전에는 일반 변경과 staged 변경을 각각 모아서 붙임.
        diff = run_git("diff", "--no-ext-diff", "--unified=3", "--", ".")
        diff += run_git("diff", "--cached", "--no-ext-diff", "--unified=3", "--", ".")
    return GitSnapshot(status=status, diff=diff, branch=branch)


def mask_sensitive(text):
    """safe mode에서 흔한 토큰·이메일·비밀값을 마스킹한다."""
    # AI한테 보내기 전에 혹시 섞여 있을 만한 비밀값을 가림.
    # 완벽한 보안 검색기는 아니고, 자주 나오는 형태를 막는 안전장치임.
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
    # diff가 너무 크면 토큰도 아깝고 AI도 핵심을 놓칠 수 있어서 잘라 보냄.
    lines = diff.splitlines()
    selected = []
    file_count = 0
    truncated = False
    for line in lines:
        if line.startswith("diff --git "):
            # 파일 수 제한을 넘으면 뒤쪽 파일은 여기서 멈춤.
            if file_count >= max_files:
                truncated = True
                break
            file_count += 1
        if len(selected) >= max_lines:
            # 파일 수와 별개로 전체 줄 수도 제한함.
            truncated = True
            break
        selected.append(line)
    if len(selected) < len(lines):
        truncated = True
    if truncated:
        # 잘렸다는 사실은 AI가 알아야 하니까 안내 문구를 붙임.
        selected.append(
            f"[SAFE MODE: diff를 최대 {max_files}개 파일, {max_lines}줄로 제한했습니다]"
        )
    return "\n".join(selected)


def prepare_diff(diff, safe_mode, max_files, max_lines):
    # safe mode가 꺼져 있으면 원본 diff를 그대로 쓰고,
    # 켜져 있으면 마스킹과 크기 제한을 둘 다 적용함.
    if not safe_mode:
        return diff
    return limit_diff(mask_sensitive(diff), max_files, max_lines)


def build_messages(command, snapshot, safe_mode, max_files, max_lines):
    # Git 정보와 출력 규칙을 AI가 이해할 수 있는 메시지로 포장하는 곳임.
    diff = prepare_diff(snapshot.diff, safe_mode, max_files, max_lines)
    output_format = (
        "COMMIT_TITLE: 한 줄 제목\nCOMMIT_BODY:\n- 선택적 본문 불릿"
        if command == "commit"
        else "PR_TITLE: 한 줄 제목\nPR_BODY:\n## Why\n- 불릿\n\n## What\n- 불릿\n\n## How to Test\n- 불릿"
    )
    instruction = (
        # 없는 테스트 결과나 변경 내용을 AI가 지어내지 못하게 선을 그어 둠.
        "Git status와 diff만 근거로 작성하세요. 없는 사실f, 테스트 결과, 수치, 파일 변경을 만들지 마세요. "
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
    # 네이토는 OpenAI 호환 API라서 여기서 HTTP POST 한 번 날리면 됨.
    # commit/pr 초안은 최소한의 응답 길이가 필요해서, 너무 작은 값은 서버가 빈 결과를 돌려주기 쉽다.
    max_tokens = max(max_tokens, 256)

    def send_request(payload_data):
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
                # 응답은 JSON으로 받고 아래에서 필요한 텍스트만 꺼냄.
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            # 서버가 4xx/5xx를 주면 응답 일부를 같이 보여줘야 원인을 찾기 쉬움.
            detail = error.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"AI API HTTP {error.code}: {detail}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"AI API 네트워크 오류: {error.reason}") from error
        except TimeoutError as error:
            raise RuntimeError("AI API 요청 시간이 초과되었습니다") from error
        except json.JSONDecodeError as error:
            raise RuntimeError("AI API 응답을 JSON으로 해석하지 못했습니다") from error

        try:
            # OpenAI 호환 응답의 첫 번째 선택지에서 AI 답변을 가져옴.
            choice = data["choices"][0]
            finish_reason = choice.get("finish_reason")
            content = choice.get("message", {}).get("content", "")
            if isinstance(content, list):
                # 일부 모델은 content를 문자열이 아니라 조각 목록으로 줌.
                content = "\n".join(
                    part.get("text", "") for part in content if isinstance(part, dict)
                )
            content = str(content).strip()
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("AI API 응답 형식이 예상과 다릅니다") from error
        if not content:
            if finish_reason == "length":
                raise RuntimeError(
                    "AI API 응답이 max_tokens 제한에 걸려 비어 있습니다. "
                    "응답 길이를 더 크게 설정해 다시 시도하세요."
                )
            raise RuntimeError("AI API 응답에 생성된 내용이 없습니다")
        return content

    payload_data = {"model": model, "messages": messages}
    if not re.match(r"^(?:gpt-5|o[1-9])", model.lower()):
        # 네이토의 GPT-5 계열은 temperature를 보내면 에러가 나서 빼는 거임.
        payload_data["temperature"] = temperature

    payload_data["max_tokens"] = max_tokens
    try:
        return send_request(payload_data)
    except RuntimeError as error:
        detail = str(error)
        if "max_tokens" not in detail.lower() and "max_completion_tokens" not in detail.lower():
            raise
        fallback_payload = {k: v for k, v in payload_data.items() if k != "max_tokens"}
        fallback_payload["max_completion_tokens"] = max_tokens
        return send_request(fallback_payload)


def clean_generated_text(text):
    # AI가 코드 펜스로 감싸도 최종 출력에는 펜스를 남기지 않음.
    return re.sub(r"```(?:text|markdown)?\s*|```", "", text, flags=re.IGNORECASE).strip()


def parse_commit(text):
    # AI가 약속한 COMMIT_TITLE/BODY 형식을 지키는지 확인하고 다듬음.
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
        # AI가 라벨을 빼먹어도 첫 줄을 제목으로 쓰는 최소한의 복구 로직임.
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
        # 본문이 불릿 형식이 아니면 우리가 앞에 -를 붙여서 통일함.
        body = "\n".join(f"- {line}" for line in body_lines)
    return title, body


def section_body(body, name, fallback):
    # PR의 각 섹션을 찾아오고, AI가 비워 두면 안전한 기본 문장을 넣음.
    pattern = rf"(?ims)^##\s*{re.escape(name)}\s*$([\s\S]*?)(?=^##\s+|\Z)"
    match = re.search(pattern, body)
    content_lines = [line.strip() for line in (match.group(1).strip() if match else "").splitlines() if line.strip()]
    if not any(line.startswith("-") for line in content_lines):
        content_lines.insert(0, f"- {fallback}")
    return "\n".join(content_lines)


def parse_pr(text, snapshot):
    # AI의 PR 응답을 제목 + Why/What/How to Test 구조로 강제함.
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
        # 라벨이 없어도 제목과 섹션을 최대한 건져서 살림.
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
    # 줄 수, 파일 수, timeout 같은 값에 0이나 음수가 들어오지 않게 함.
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("0보다 큰 정수를 입력하세요")
    return number


def temperature(value):
    # 모델 temperature는 API가 받는 범위 안에서만 허용함.
    number = float(value)
    if not 0 <= number <= 2:
        raise argparse.ArgumentTypeError("temperature는 0~2 범위여야 합니다")
    return number
    


def add_options(parser, suppress_defaults=False):
    # 최상위 parser와 commit/pr parser가 같은 옵션을 쓰니까 여기서 재사용함.
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
    # 터미널 입력을 이해할 argparse 메뉴판을 만드는 부분임.
    parser = argparse.ArgumentParser(description="Git 변경 사항으로 AI 커밋/PR 초안을 생성합니다.")
    add_options(parser)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("commit", "pr"):
        command_parser = commands.add_parser(command, help=f"{command} 초안 생성")
        add_options(command_parser, suppress_defaults=True)
    return parser


def print_interactive_help():
    # CLI를 켜 놓고 help를 입력했을 때 보여줄 짧은 사용법임.
    print(
        "사용법:\n"
        "  commit [옵션]       커밋 메시지 초안 생성\n"
        "  pr [옵션]           PR 초안 생성\n"
        "  help                도움말 보기\n"
        "  exit, quit          CLI 종료\n\n"
        "예시:\n"
        "  commit --safe-mode\n"
        "  pr --safe-mode --max-lines 100"
    )


def interactive_cli():
    # 프로그램을 매번 껐다 켜지 않고 여기서 commit/pr을 계속 입력하는 모드.
    parser = build_parser()
    print("AI Git 도우미를 시작했습니다. help를 입력하면 사용법을 볼 수 있습니다.")
    while True:
        try:
            raw_command = input("ai-git> ").strip()
        except (EOFError, KeyboardInterrupt):
            # Ctrl+D나 Ctrl+C를 눌러도 이상한 traceback 없이 나가게 함.
            print("\nCLI를 종료합니다.")
            return 0
        if not raw_command:
            continue
        if raw_command.lower() in {"exit", "quit", "q"}:
            # 종료 명령은 argparse까지 보낼 필요 없이 바로 처리함.
            print("CLI를 종료합니다.")
            return 0
        if raw_command.lower() in {"help", "?"}:
            print_interactive_help()
            continue
        try:
            # 따옴표가 들어간 옵션도 명령줄처럼 나눠 줌.
            command_args = shlex.split(raw_command)
        except ValueError as error:
            print(f"[ERROR] 명령어 따옴표를 확인하세요: {error}", file=sys.stderr)
            continue
        try:
            # 잘못된 명령은 CLI 전체를 죽이지 말고 다음 입력을 기다림.
            args = parser.parse_args(command_args)
        except SystemExit:
            continue
        run_command(args)


def env_value(*names):
    # 여러 환경변수 이름 중 실제로 값이 들어 있는 첫 번째 것을 사용함.
    return next((os.getenv(name, "").strip() for name in names if os.getenv(name, "").strip()), "")


def load_dotenv():
    # 외부 패키지 없이 .env를 읽는 부분임. 이미 설정된 환경변수는 덮어쓰지 않음.
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
            # API 키를 코드에 직접 쓰지 않고 환경변수로 넣어 둠.
            os.environ[name.strip()] = value.strip().strip("\"'")


def resolve_options(args):
    # 명령줄 옵션 → .env → 기본값 순서로 최종 설정을 결정함.
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


def run_command(args):
    # 실제 한 번의 commit/pr 요청을 처리하는 본체임.
    options = resolve_options(args)
    try:
        snapshot = collect_snapshot()
    except (OSError, RuntimeError) as error:
        print(f"[ERROR] {error}", file=sys.stderr)
        return 1

    changed_files = [line for line in snapshot.status.splitlines() if line.strip()]
    if not changed_files:
        # 바뀐 게 없으면 AI를 부를 이유도 없으니 여기서 끝냄.
        print("[INFO] 변경 사항이 없습니다. 이번 요청을 건너뜁니다.")
        return 0

    print(f"[INFO] Git status 수집 완료: {len(changed_files)}개 파일 변경 감지")
    print(f"[INFO] Git diff 수집 완료: {len(snapshot.diff.splitlines())}줄")
    if not options["api_key"]:
        # 키가 없으면 인증 실패할 게 뻔하니 요청 전에 알려 줌.
        print(
            "[ERROR] NAITO_API_KEY 환경변수가 설정되지 않았습니다. "
            '예: export NAITO_API_KEY="YOUR_KEY"',
            file=sys.stderr,
        )
        return 1
    if not options["api_url"]:
        # 주소가 없을 때 엉뚱한 곳으로 요청하지 않게 막음.
        print(
            "[ERROR] NAITO_API_URL 환경변수가 설정되지 않았습니다. "
            '네이토가 안내한 Chat Completions 주소를 .env에 입력하세요.',
            file=sys.stderr,
        )
        return 1

    print("[INFO] Naito AI API 요청 중... (1회)")
    try:
        # 한 번의 요청으로 초안을 만들고, 실제 commit/push는 하지 않음.
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
            # 커밋은 제목과 선택적 본문만 출력함.
            title, body = parse_commit(generated)
            print("[DONE] 커밋 메시지 생성 완료\n\n--- Commit Message ---")
            print(title)
            if body:
                print(f"\n{body}")
        else:
            # PR은 제목과 세 개의 설명 섹션을 출력함.
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


def main(argv=None):
    # 인자가 있으면 단발 실행, 없으면 계속 입력하는 대화형 CLI로 들어감.
    load_dotenv()
    command_args = sys.argv[1:] if argv is None else argv
    if not command_args:
        return interactive_cli()
    args = build_parser().parse_args(command_args)
    return run_command(args)


if __name__ == "__main__":
    raise SystemExit(main())
