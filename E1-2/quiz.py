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
        self.quizzes = [
            Quiz("Python의 창시자는 누구일까요?", ["Guido van Rossum", "Linus Torvalds", "James Gosling", "Bjarne Stroustrup"], 1, "파이썬 세계에서는 오랫동안 '종신 자비로운 독재자(BDFL)'라 불렸습니다."),
            Quiz("다음 중 Python의 웹 프레임워크가 아닌 것은?", ["Django", "Flask", "FastAPI", "Spring"], 4, "이것은 Java 생태계의 가장 대표적인 프레임워크입니다."),
            Quiz("Git을 처음 개발한 사람은 누구일까요?", ["Bill Gates", "Linus Torvalds", "Steve Jobs", "Mark Zuckerberg"], 2, "Linux 커널의 창시자이기도 합니다."),
            Quiz("데이터를 키-값 쌍으로 저장하는 Python의 기본 자료형은?", ["List", "Tuple", "Dictionary", "Set"], 3, "중괄호 {}를 사용하며 JSON 데이터와 구조가 매우 유사합니다."),
            Quiz("Python에서 클래스의 생성자 메서드 이름은?", ["__init__", "__start__", "constructor", "init"], 1, "밑줄(underscore) 두 개로 시작하고 끝납니다.")
        ]
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
