# 2. 저장소(Repository) 와 커밋(Commit) 뼈대 만들기

from model import Commit

# 레포지토리 클래스 정의
class Repository:
    def __init__(self):
        self.commits = {}   # 해시(키) - 커밋(밸류) 값을 저장할 딕셔너리
        self.current_user = None # 현재 유저 이름
        self.branch = {}    # 브랜치 이름(키) - 커밋 해시(밸류) 값을 저장할 딕셔너리
        self.HEAD = None    # 현재 체크아웃된 브랜치 이름 (예 : "main")

        self.inverted_index_keyword = {}  # 단어(소문자) -> 커밋 해시들의 리스트(Set) 
        self.inverted_index_author = {}   # 작성자(소문자) -> 커밋 해시들의 리스트(Set)

    def init(self, user_name):
        self.current_user = user_name
        self.commits.clear() # 기존에 데이터가 있으면 날려버림
        self.branches.clear()
        self.HEAD = "main"
        self.branches["main"] = None

        self.inverted_index_keyword.clear() # 키워드 인덱스 초기화
        self.inverted_index_author.clear()  # 작성자 인덱스 초기화


    def commit(self, message):
        if not self.current_user:
            raise ValueError("저장소가 초기화되지 않았나봐요. INIT을 먼저 해주세요")
        
        # 현재 브렌치가 가리키는 커밋이 없지 않다면, 그것이 새 커밋의 부모가 됨
        parent = []
        if self.branch[self.HEAD] is not None:
            parent.append(self.branches[self.HEAD])

        # 새 커밋 생성 
        new_commit = Commit(message, self.current_user, parent)

        # 딕셔너리에 저장
        self.commits[new_commit.hash] = new_commit

        # 커밋을 했으니, 현재 브랜치가 방금 만든 새 커밋을 가리키도록 업데이트
        self.branches[self.HEAD] = new_commit.hash

        # 작성자 인덱스 업데이트
        author_lower = new_commit.author.lower()
        # 만약에 작성자가 작성자해시에 없다면 작성자인덱스에 키로 추가
        if author_lower not in self.inverted_index_author:
            self.inverted_index_author[author_lower] = set() 
        
        # 해시 값을 더해줌
        self.inverted_index_author[author_lower].add(new_commit.hash)

        tokens = message.lower().split()
        for token in tokens:
            # 만약 토큰이 역색인 키워드에 없다면 
            if token not in self.inverted_index_keyword:
                # 토큰을 키로하는 키워드를 생성
                self.inverted_index_keyword[token] = set()
            # 키에 새 해시값을 추가
            self.inverted_index_keyword[token].add(new_commit.hash)

        return new_commit

    def search(self, keyword, is_author=False):


        

    # 브랜치 기능 구현 함수 정의
    def branch(self, branch_name):
        # 만약 브랜치이름이 브랜치 딕셔너리에 이미 존재한다면
        if branch_name in self.branches:
            #에러 출력
            raise ValueError(f"{branch_name} 은 이미 존재하는 브랜치에요.")
        # 새 브랜치는 현재 헤드가 가리키고 있는 커밋을 똑같이 가리키며 생성
        self.branches[branch_name] = self.branches[self.HEAD]
    
    # 스위치 기능 구현 함수 정의
    def switch(self, branch_name):
        # 만약 브랜치이름이 브랜치 딕셔너리에 없다면
        if branch_name not in self.branches:
            raise ValueError(f"{branch_name} 브랜치는 존재하지 않아요")
        # 헤드가 가리키는 브랜치를 지정한 브랜치로 변경
        self.HEAD = branch_name
        

