# REPL(Read-Eval-Print Loop) 구조로 미니 깃 구현
# 명령어는 대소문자를 구분하지 않는다. (INIT,init 모두 가능)
# 커밋 메시지나 사용자 이름 등은 공백을 포함할 수 있으며, " "로 묶는다.

import sys
import shlex
from repository import Repository

# CLI 메인 뼈대함수를 정의
def main():
    repo = Repository() # 레포지토리 객체 생성
    print("Mini Git 을 시작합니다~ (종료 : exit 혹은 quit)")

    # while True 으로 둠으로써 무한루프를 돌린다.
    while True:
        try:
            # 1. 프롬프트 출력 및 사용자 입력 받기
            user_input = input("Mini-Git > ").strip()

            if not user_input:
                continue  #아무것도 입력하지 않았으면 다시 시작

            # 2. shlex 를 통해 따옴표 안의 공백을 유지하며 분리.
            # 예: 'commit "add feature"' -> ['commit', 'add feature']
            args = shlex.split(user_input)

            # 3. 첫 번째 단어를 명령어로 분리 (대소문자 구분 없도록 대문자로 통일)
            command = args[0].upper()

            # 종료 명령어 처리
            if command == "EXIT" or command == "QUIT":
                print("Mini Git 을 종료할게여~")
                break

            # 4. 명령어 라우팅
            if command == "INIT":
                if len(args) < 2:
                    print("잘못된 인자들입니다. 예 : INIT <user_name>")
                    continue 
                user_name = args[1]
                repo.init(user_name)
                print(f"저장소가 {user_name} 으로 초기화 됐어여!")

            # 커맨드가 커밋일 때
            elif command == "COMMIT":
                #인자가 2개 미만일 경우에는 오류 표시 후 contine
                if len(args) < 2:
                    print("잘못된 인자들입니다. 예 : COMMIT <message>")
                    continue
                message = args[1]
                # 레포지토리 객체의 커밋함수 실행
                try:
                    new_commit = repo.commit(message)
                    print(f"커밋 완료: {new_commit}")
                # repository에서 raise한 밸류에러 잡기
                except ValueError as e:
                    print(f"오류 발생: {e}")
            
            elif command == "BRANCH":
                #인자가 2개 미만일 경우에 오류 표시
                if len(args) < 2:
                    print("잘못된 인자들입니다. 예 : BRANCH <branch_name>")
                    continue
                branch_name = args[1]
                try:
                    repo.branch(branch_name)
                    print(f"브랜치 생성 완료했습니다~:{branch_name}")
                except ValueError as e:
                    print(f"오류 발생")
            
            elif command == "SWITCH":
                if len(args) < 2:
                    print("잘못된 인자들입니다. 예 : SWITCH <branch_name>")
                    continue
                branch_name = args[1]
                try:
                    repo.switch(branch_name)
                    print(f"브랜치 변경완료! : 현재 브랜치 -> {branch_name}")
                except ValueError as e:
                    print(f"오류 발생 : {e}")
            else:
                print(f"알 수 없는 명령어에요! : {command}")

        except ValueError as e:
            print(f"입력 오류가 발생했어요 : {e}")

        except EOFError:
            break

        except Exception as e:
            print(f"알 수 없는 오류가 발생했어요 : {e}")


if __name__ == "__main__":
    main()