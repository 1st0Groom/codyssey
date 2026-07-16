from core.redis_store import MiniRedisStore
from cli import run_cli

def main():
    # 1. 뼈대부터 하나하나 만든 메모리 데이터베이스 엔진을 켜다.
    print("Welcome to Mini Redis!")
    store = MiniRedisStore()

    # 2. CLI 를 켜
    run_cli(store)

if __name__ == "__main__":
    main()
