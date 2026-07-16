import shlex

def run_cli(store):
    """
    무한 루프를 돌며 사용자의 입력을 받고 결과를 출력하는 REPL 함수입니다.
    """
    while True:
        try:
            # 1. 프롬프트 출력 및 입력 대기
            user_input = input("mini-redis> ")
            if not user_input.strip():
                continue

            # 2. 명령어 파싱 (shlex.split을 쓰면 따옴표(" ") 안의 공백을 잘 유지해 줍니다!)
            try:
                tokens = shlex.split(user_input)
            except ValueError:
                print("(error) ERR unbalanced quotes in input")
                continue

            cmd = tokens[0].upper() # 명령어는 항상 대문자로 변환해서 비교
            args = tokens[1:]       # 명령어 뒤에 따라오는 인자들

            # 3. 종료 명령어
            if cmd in ("EXIT", "QUIT"):
                break

            # 4. 명령어 매칭 및 실행
            if cmd == "SET":
                if len(args) != 2:
                    print("(error) ERR wrong number of arguments for 'SET' command")
                else:
                    print(store.SET(args[0], args[1]))

            elif cmd == "GET":
                if len(args) != 1:
                    print("(error) ERR wrong number of arguments for 'GET' command")
                else:
                    print(store.GET(args[0]))

            elif cmd == "DEL":
                if len(args) != 1:
                    print("(error) ERR wrong number of arguments for 'DEL' command")
                else:
                    print(store.DEL(args[0]))

            elif cmd == "EXISTS":
                if len(args) != 1:
                    print("(error) ERR wrong number of arguments for 'EXISTS' command")
                else:
                    print(store.EXISTS(args[0]))

            elif cmd == "DBSIZE":
                if len(args) != 0:
                    print("(error) ERR wrong number of arguments for 'DBSIZE' command")
                else:
                    print(store.DBSIZE())

            elif cmd == "KEYS":
                if len(args) != 0:
                    print("(error) ERR wrong number of arguments for 'KEYS' command")
                else:
                    print(store.KEYS())

            elif cmd == "CONFIG":
                if len(args) != 3 or args[0].upper() != "SET":
                    print("(error) ERR wrong number of arguments for 'CONFIG SET' command")
                else:
                    print(store.CONFIG_SET(args[1], args[2]))

            elif cmd == "INFO":
                if len(args) != 1 or args[0].lower() != "memory":
                    print("(error) ERR wrong number of arguments for 'INFO memory' command")
                else:
                    print(store.INFO_memory())

            elif cmd == "EXPIRE":
                if len(args) != 2:
                    print("(error) ERR wrong number of arguments for 'EXPIRE' command")
                else:
                    try:
                        seconds = int(args[1])
                        print(store.EXPIRE(args[0], seconds))
                    except ValueError:
                        print("(error) ERR value is not an integer or out of range")

            elif cmd == "TTL":
                if len(args) != 1:
                    print("(error) ERR wrong number of arguments for 'TTL' command")
                else:
                    print(store.TTL(args[0]))

            else:
                # 모르는 명령어일 때
                print(f"(error) ERR unknown command '{cmd}'")

        # Ctrl+C (KeyboardInterrupt) 또는 Ctrl+D (EOFError) 를 눌렀을 때 안전하게 종료
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break
        except Exception as e:
            print(f"(error) Internal server error: {e}")