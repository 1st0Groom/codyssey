import sys
import random

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
                self.play_quiz()
            elif choice == '2':
                self.add_quiz()
            elif choice == '3':
                self.list_quizzes()
            elif choice == '4':
                self.show_score()
            elif choice == '5':
                print("게임을 종료합니다. 안녕히 가세요! 👋")
                sys.exit(0)
            else:
                print("⚠️ 잘못된 입력입니다. 1-5 사이의 숫자를 입력하세요.\n")

    def add_quiz(self):
        print("\n📌 새로운 퀴즈를 추가합니다.")
        question = input("문제를 입력하세요: ").strip()
        if not question:
            print("⚠️ 빈 입력입니다. 퀴즈 추가를 취소합니다.")
            return

        choices = []
        for i in range(1, 5):
            while True:
                choice = input(f"선택지 {i}: ").strip()
                if not choice:
                    print("⚠️ 빈 입력입니다. 다시 입력해주세요.")
                else:
                    choices.append(choice)
                    break
        
        while True:
            ans_input = input("정답 번호 (1-4): ").strip()
            if not ans_input.isdigit() or not (1 <= int(ans_input) <= 4):
                print("⚠️ 1에서 4 사이의 숫자를 입력하세요.")
                continue
            answer = int(ans_input)
            break

        hint = input("힌트를 입력하세요 (없으면 엔터): ").strip()
        self.quizzes.append(Quiz(question, choices, answer, hint))
        print("✅ 퀴즈가 성공적으로 추가되었습니다!")

    def play_quiz(self):
        if not self.quizzes:
            print("⚠️ 등록된 퀴즈가 없습니다! 퀴즈를 먼저 추가해주세요.")
            return

        # 랜덤 출제 로직
        play_list = self.quizzes.copy()
        random.shuffle(play_list)

        print(f"\n📝 퀴즈를 시작합니다! (총 {len(play_list)}문제)")
        
        score = 0
        for i, q in enumerate(play_list, 1):
            q.display(i, len(play_list))
            used_hint = False
            
            while True:
                user_input = input("정답 입력 (힌트 보기: 'h' 또는 'hint'): ").strip().lower()
                
                if not user_input:
                    print("⚠️ 빈 입력입니다. 다시 입력해주세요.")
                    continue
                    
                if user_input in ['h', 'hint']:
                    if not used_hint:
                        print(f"💡 힌트: {q.hint}")
                        used_hint = True
                    else:
                        print("⚠️ 힌트를 이미 사용했습니다.")
                    continue
                    
                if not user_input.isdigit():
                    print("⚠️ 숫자 정답을 입력하거나, 힌트를 보려면 'h'를 입력하세요.")
                    continue
                    
                answer_num = int(user_input)
                if not 1 <= answer_num <= len(q.choices):
                    print(f"⚠️ 1에서 {len(q.choices)} 사이의 번호를 입력하세요.")
                    continue
                
                # 정답 확인
                if q.check_answer(user_input):
                    # 힌트 사용 시 0.5점(점수 차감 로직 - 보너스 과제) 부여
                    earned = 0.5 if used_hint else 1
                    print("✅ 정답입니다!" + (" (힌트 사용으로 0.5점)" if used_hint else ""))
                    score += earned
                else:
                    print(f"❌ 오답입니다! 정답은 {q.answer}번입니다.")
                break

        print(f"\n{'='*40}")
        print(f"🏆 결과: {len(play_list)}문제 중 총 {score}점 획득! ({int(score/len(play_list)*100)}점)")
        if score > self.best_score:
            print("🎉 새로운 최고 점수입니다!")
            self.best_score = score
        print(f"{'='*40}")

    def list_quizzes(self):
        if not self.quizzes:
            print("\n📋 현재 등록된 퀴즈가 없습니다.")
            return
            
        print(f"\n📋 등록된 퀴즈 목록 (총 {len(self.quizzes)}개)")
        print("-" * 40)
        for i, q in enumerate(self.quizzes, 1):
            print(f"[{i}] {q.question}")
        print("-" * 40)

    def show_score(self):
        print("\n" + "="*40)
        print(f"🏆 현재 최고 점수: {self.best_score}점")
        print("="*40)

if __name__ == "__main__":
    try:
        game = QuizGame()
        game.run()
    except (KeyboardInterrupt, EOFError):
        print("\n⚠️ 비정상 종료를 감지했습니다. 프로그램을 안전하게 종료합니다.")
        sys.exit(0)
