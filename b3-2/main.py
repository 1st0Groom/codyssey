# 실제 로직은 한 파일에 몰아두고, 이 파일은 실행 진입점만 담당하게 함.
from ai_git_helper import main


if __name__ == "__main__":
    # python3 main.py를 실행하면 여기서 프로그램이 시작됨.
    raise SystemExit(main())
