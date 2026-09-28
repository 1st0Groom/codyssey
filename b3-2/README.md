# AI Git 설명 도우미

Git 변경 사항을 네이토(NAITO) AI API에 전달해 커밋 메시지와 Pull Request 초안을 출력하는 터미널 도구입니다. 실제 `git commit`, `git push`, GitHub PR 생성은 하지 않습니다.

## 실행

Python 3.10 이상, 추가 패키지 없이 실행합니다.

```bash
cd /home/camus/workspace/codyssey/b3-2
export NAITO_API_KEY="네이토에서 발급받은 키"
export NAITO_API_URL="네이토가 안내한 OpenAI 호환 Chat Completions 주소"
export NAITO_MODEL="사용할 모델명"

python3 main.py commit --safe-mode
python3 main.py pr --safe-mode
```

`NAITO_API_URL`는 필수입니다. 코디세이 네이토 OpenAI Base URL은 `https://copa.codyssey.kr/v1`이며, 코드에는 Chat Completions 주소를 입력합니다. 주소가 없으면 잘못된 서버로 요청하지 않고 종료합니다. `AI_API_KEY`, `AI_API_URL`, `AI_MODEL`도 호환용으로 지원합니다.

## 옵션

```bash
python3 main.py commit --model MODEL --temperature 0.2 --max-tokens 2000
python3 main.py pr --safe-mode --max-files 10 --max-lines 200
```

- `--temperature`: 0~2
- `--max-tokens`: 응답 최대 토큰
- `--safe-mode`: 토큰·이메일·비밀번호·개인키를 마스킹하고 diff를 기본 10개 파일·200줄로 제한
- `--api-url`: 네이토 API 주소를 일회성으로 변경

네이토의 GPT-5 계열 모델은 `temperature`를 지원하지 않으므로 해당 요청 필드는 자동으로 생략합니다.

변경 사항이 없으면 API를 호출하지 않습니다. API 요청은 `commit` 또는 `pr` 한 번당 1회입니다.

## 출력 형식

커밋:

```text
--- Commit Message ---
fix: validate empty input
- reject empty command before parsing
```

PR:

```markdown
## Why
- 변경 배경

## What
- 핵심 변경 사항

## How to Test
- 테스트 방법
```

생성된 문구는 사람이 검토한 뒤 사용하세요. diff에 민감정보가 있을 수 있으므로 `--safe-mode` 사용을 권장합니다.

## 테스트

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_ai_git_helper.py
python3 -m py_compile main.py ai_git_helper.py
```
