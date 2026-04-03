import json
import os
import sys

STATE_FILE = "state.json"

class Quiz:
    def __init__(self, question, choices, answer):
        self.question = question
        self.choices = choices
        self.answer = answer

    def show_question(self, index=1, total=1):
        print(f"\n{'-'*40}")
        print(f"[문제 {index}/{total}]")
        print(self.question, "\n")
        
        for i, choice in enumerate(self.choices, 1):
            print(f"{i}. {choice}")
            
    def check_answer(self, user_answer):
        try:
            return int(user_answer) == self.answer
        except ValueError:
            return False


class QuizGame:
    def __init__(self):
        self.quizzes = []
        self.best_score = 0
        self.load_data()

    def load_data(self):
        file_path = os.path.join(os.path.dirname(__file__), STATE_FILE)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.best_score = data.get("best_score", 0)
                    for q in data.get("quizzes", []):
                        self.quizzes.append(Quiz(q["question"], q["choices"], q["answer"]))
                print(f"📂 저장된 데이터를 불러왔습니다. (퀴즈 {len(self.quizzes)}개, 최고점수 {self.best_score}점)")
            except Exception as e:
                print("⚠️ 데이터 파일을 불러오는데 실패했습니다.", e)
                
    def save_data(self):
        file_path = os.path.join(os.path.dirname(__file__), STATE_FILE)
        data = {
            "quizzes": [{"question": q.question, "choices": q.choices, "answer": q.answer} for q in self.quizzes],
            "best_score": self.best_score
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("⚠️ 데이터를 저장하는데 실패했습니다.", e)

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
        if not self.quizzes:
            print("⚠️ 등록된 퀴즈가 없습니다! 퀴즈를 먼저 추가해주세요.")
            return

        print(f"\n📝 퀴즈를 시작합니다! (총 {len(self.quizzes)}문제)")
        
        score = 0
        for i, q in enumerate(self.quizzes, 1):
            q.show_question(i, len(self.quizzes))
            while True:
                user_input = input("정답 입력: ").strip()
                if not user_input:
                    print("⚠️ 빈 입력입니다. 다시 입력해주세요.")
                    continue
                if not user_input.isdigit():
                    print("⚠️ 숫자만 입력해주세요.")
                    continue
                answer_num = int(user_input)
                if not 1 <= answer_num <= len(q.choices):
                    print(f"⚠️ 1에서 {len(q.choices)} 사이의 숫자를 입력하세요.")
                    continue
                break
                
            if q.check_answer(user_input):
                print("✅ 정답입니다!")
                score += 1
            else:
                print(f"❌ 오답입니다! 정답은 {q.answer}번입니다.")

        print(f"\n{'='*40}")
        print(f"🏆 결과: {len(self.quizzes)}문제 중 {score}문제 정답! ({int(score/len(self.quizzes)*100)}점)")
        if score > self.best_score:
            print("🎉 새로운 최고 점수입니다!")
            self.best_score = score
            self.save_data()
        print(f"{'='*40}")

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
