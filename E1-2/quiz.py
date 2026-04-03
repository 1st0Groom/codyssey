import json
import os
import sys

STATE_FILE = "state.json"

class Quiz:
    def __init__(self, question, choices, answer):
        self.question = question
        self.choices = choices
        self.answer = answer

    def show_question(self):
        # TODO: Implement showing the question and choices
        pass

    def check_answer(self, user_answer):
        # TODO: Implement logic to check answer
        pass


class QuizGame:
    def __init__(self):
        self.quizzes = []
        self.best_score = 0
        self.load_data()

    def load_data(self):
        # TODO: Load from state.json
        pass

    def save_data(self):
        # TODO: Save to state.json
        pass

    def display_menu(self):
        print("\n" + "="*40)
        print("        🎯 나만의 퀴즈 게임 🎯")
        print("="*40)
        print("1. 퀴즈 풀기")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록")
        print("4. 점수 확인")
        print("5. 종료")
        print("="*40)

    def run(self):
        while True:
            self.display_menu()
            choice = input("선택: ").strip()
            
            if choice == "1":
                self.play_quiz()
            elif choice == "2":
                self.add_quiz()
            elif choice == "3":
                self.list_quizzes()
            elif choice == "4":
                self.show_score()
            elif choice == "5":
                print("다음에 또 만나요! 👋")
                sys.exit(0)
            else:
                print("⚠️ 잘못된 입력입니다. 1-5 사이의 숫자를 입력하세요.")

    def play_quiz(self):
        print("📝 퀴즈 풀기 기능 준비 중...")

    def add_quiz(self):
        print("📌 퀴즈 추가 기능 준비 중...")

    def list_quizzes(self):
        print("📋 퀴즈 목록 기능 준비 중...")

    def show_score(self):
        print("🏆 점수 확인 기능 준비 중...")


if __name__ == "__main__":
    try:
        game = QuizGame()
        game.run()
    except (KeyboardInterrupt, EOFError):
        print("\n프로그램을 안전하게 종료합니다.")
        sys.exit(0)
