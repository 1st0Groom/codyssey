import time
import random



# Git 저장소, 커밋을 담을 클래스를 정의
class Commit:
    def __init__(self, message, authorm, parents=None):
        # 16진수 난수를 이용해 6자리 해시 생성 (충돌 가능성 매우 낮음)
        self.hash = f"{random.randint(0, 0xFFFFFF):06x}"
        self.message = message
        self.author = authorm
        self.timestamp = time.time()
        self.parents = parents if parents else []

    # 프린트할 때 예쁘게 보이도록 만드는 함수
    def __str__(self):
        # 년도-달-일 시간:분:초 형태로 현재 시간 변환
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        # 커밋 정보를 문자열로 반환
        return f"[{self.hash}] {self.message} ({self.author} , {time_str})"
    