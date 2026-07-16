import sys

#1. 클래스 역할 분담하기
 
class Quiz:
    def __init__(self, question, choices, answer):
        self.question = question    # 질문 (문자열)
        self.choices = choices      # 보기 5개 (리스트)
        self.answer = answer        # 정답 번호 (1~4 사이 정수)

    def __str__(self):
        # 퀴즈를  출력했을 때 "Q: 질문" 양식으로 보여주는 기능
        return f"Q: {self.question}"

class QuizGame:
    def __init__(self): 
        self.quizzes = []
        self.best_score =0