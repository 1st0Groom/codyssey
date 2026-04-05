import sys

class Quiz:
    def __init__(self, question, choices, answer, hint=""):
        self.question = question
        self.choices = choices
        """answer는 1에서 4 사이의 정수 (선택지 번호)"""
        self.answer = answer
        self.hint = hint

    def display(self, index=1, total=1):
        print(f"\n{'-'*40}")
        print(f"[문제 {index}/{total}]")
        print(self.question, "\n")
        for i, choice in enumerate(self.choices, 1):
            print(f"{i}. {choice}")
            
    def check_answer(self, user_input):
        try:
            return int(user_input) == self.answer
        except ValueError:
            return False

class QuizGame:
    def __init__(self):
        # 향후 퀴즈 목록과 점수를 저장할 변수
        self.quizzes = []
        self.best_score = 0
        
    def display_menu(self):
        print("\n========================================")
        print("        🎯 나만의 퀴즈 게임 🎯")
        print("========================================")
        print("1. 퀴즈 풀기")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록")
        print("4. 점수 확인")
        print("5. 종료")
        print("========================================")

    def run(self):
        while True:
            self.display_menu()
            choice = input("선택: ").strip()
            
            if not choice:
                print("⚠️ 빈 입력입니다. 다시 입력해주세요.\n")
                continue
                
            if choice == '1':
                print("📌 퀴즈 풀기 기능 준비 중...")
            elif choice == '2':
                print("📌 퀴즈 추가 기능 준비 중...")
            elif choice == '3':
                print("📌 퀴즈 목록 기능 준비 중...")
            elif choice == '4':
                print("📌 점수 확인 기능 준비 중...")
            elif choice == '5':
                print("게임을 종료합니다. 안녕히 가세요! 👋")
                sys.exit(0)
            else:
                print("⚠️ 잘못된 입력입니다. 1-5 사이의 숫자를 입력하세요.\n")

if __name__ == "__main__":
    try:
        game = QuizGame()
        game.run()
    except (KeyboardInterrupt, EOFError):
        print("\n⚠️ 비정상 종료를 감지했습니다. 프로그램을 안전하게 종료합니다.")
        sys.exit(0)
