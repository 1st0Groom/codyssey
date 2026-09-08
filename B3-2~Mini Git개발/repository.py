from commit import Commit
from collections import deque
from utils import merge_sort


# 레포지토리 클래스 정의
class Repository:
    def __init__(self):
        self.commits = {}   # 해시(키) - 커밋(밸류) 값을 저장할 딕셔너리
        self.current_user = None # 현재 유저 이름
        self.branches = {}    # 브랜치 이름(키) - 커밋 해시(밸류) 값을 저장할 딕셔너리
        self.HEAD = None    # 현재 체크아웃된 브랜치 이름 (예 : "main")

        self.keyword_index = {}  # 단어(키) - 그 단어가 들어간 커밋 해시 목록(밸류) : 역색인
        self.author_index = {}   # 작성자(키) - 그 사람이 쓴 커밋 해시 목록(밸류) : 역색인

    def init(self, user_name):
        self.current_user = user_name
        self.commits.clear() # 기존에 데이터가 있으면 날려버림
        self.branches.clear()

        # 깃처럼 처음엔 main 브랜치 하나만 있고, 아직 커밋이 없으니 None 을 가리킨다
        self.branches["main"] = None
        self.HEAD = "main"

    def commit(self, message):
        if not self.current_user:
            raise ValueError("저장소가 초기화되지 않았나봐요. INIT을 먼저 해주세요")

        # 현재 브렌치가 가리키는 커밋이 없지 않다면, 그것이 새 커밋의 부모가 됨
        parent = []
        if self.branches[self.HEAD] is not None:
            parent.append(self.branches[self.HEAD])

        # 새 커밋 생성
        new_commit = Commit(message, self.current_user, parent)

        # 딕셔너리에 저장
        self.commits[new_commit.hash] = new_commit

        # 커밋을 했으니, 현재 브랜치가 방금 만든 새 커밋을 가리키도록 업데이트
        self.branches[self.HEAD] = new_commit.hash

        # 검색할 때 전체를 훑지 않도록, 커밋하는 이 시점에 미리 역색인을 만들어 둔다
        # 메시지를 소문자로 바꾼 뒤 공백으로 쪼개서 단어별로 이 커밋 해시를 매달아 놓는다
        words = message.lower().split()
        for word in words:
            if word not in self.keyword_index:
                self.keyword_index[word] = []  # 처음 나온 단어면 빈 목록부터 만든다
            self.keyword_index[word].append(new_commit.hash)

        # 작성자는 쪼갤 필요가 없으니 이름 통째로 키가 된다
        author = new_commit.author
        if author not in self.author_index:
            self.author_index[author] = []
        self.author_index[author].append(new_commit.hash)

        return new_commit

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

    def status(self):
        print(f"현재 브랜치 : {self.HEAD}")
        print(f"현재 브랜치가 가리키는 커밋 : {self.branches[self.HEAD]}")
        print(f"현재 유저 : {self.current_user}")
        print(f"저장소에 존재하는 브랜치들 : {list(self.branches.keys())}")

    def search(self, keyword):
        # 색인을 만들 때 소문자로 바꿨으니, 찾을 때도 똑같이 소문자로 바꿔야 매칭이 된다
        keyword = keyword.lower()

        # 없는 단어면 KeyError 대신 빈 목록을 주도록 get 을 쓴다
        return self.keyword_index.get(keyword, [])

    def search_by_author(self, author):
        return self.author_index.get(author, [])

    # 커밋 해시 - 그 커밋을 가리키는 브랜치 이름 목록 딕셔너리를 만드는 함수 정의
    def branch_decorations(self):
        # branches 는 브랜치 -> 해시 방향인데, 로그는 커밋을 돌면서 찍으니
        # 해시 -> 브랜치 방향으로 뒤집어 놔야 커밋마다 바로 꺼내 쓸 수 있다
        decorations = {}

        for branch_name, commit_hash in self.branches.items():
            # 아직 커밋이 없는 브랜치는 가리키는 커밋이 없으니 건너뛴다
            if commit_hash is None:
                continue

            if commit_hash not in decorations:
                decorations[commit_hash] = []

            # 지금 체크아웃된 브랜치는 깃처럼 HEAD -> 를 붙이고 맨 앞에 놓는다
            if branch_name == self.HEAD:
                decorations[commit_hash].insert(0, f"HEAD -> {branch_name}")
            else:
                decorations[commit_hash].append(branch_name)

        return decorations

    def log(self, sort_by=None):

        if not self.commits:
            print("저장소에 커밋이 없어요!")
            return

        # 타임스탬프나 작성자 이름을 기준으로 세울 때는 직접 구현한 병합 정렬을 쓴다
        if sort_by == "date":
            commits_list = merge_sort(list(self.commits.values()), lambda c: c.timestamp)
        elif sort_by == "author":
            commits_list = merge_sort(list(self.commits.values()), lambda c: c.author)
        # 기준을 안 주면 시계를 믿지 않고 부모 관계로 순서를 계산한다
        else:
            commits_list = self.topological_sort()

        # 어떤 커밋에 어떤 브랜치가 걸려 있는지 미리 한 번만 만들어 둔다
        decorations = self.branch_decorations()

        for commit in commits_list:
            # 브랜치가 걸린 커밋에만 (HEAD -> main, feature) 같은 꼬리표를 붙인다
            deco = decorations.get(commit.hash, [])
            deco_text = f" ({', '.join(deco)})" if deco else ""

            print(f"{commit.hash} - {commit.message} (작성자 :{commit.author} , 시간 {commit.timestamp}){deco_text}")

    def topological_sort(self):

        in_degree = {}  # 커밋별로 아직 처리 안 된 부모가 몇 개인지 세는 딕셔너리
        children = {}   # 부모 -> 자식 방향으로 뒤집은 간선 목록

        # 일단 전부 0과 빈 목록으로 초기화해 둔다
        for hash in self.commits:
            in_degree[hash] = 0
            children[hash] = []

        # 커밋은 부모만 알고 있으니, 자식 방향을 알려면 간선을 뒤집어야 한다
        for hash, commit in self.commits.items():
            for parent in commit.parents:
                children[parent].append(hash)
                in_degree[hash] += 1  # 부모가 하나 있으면 기다려야 할 선행조건이 하나 늘어난다

        # 진입차수가 0 이면 기다릴 부모가 없다는 뜻 = 최초 커밋. 여기서 출발한다
        queue = deque()
        for hash in self.commits:
            if in_degree[hash] == 0:
                queue.append(hash)

        result = []
        while queue:
            current = queue.popleft()
            result.append(self.commits[current])

            for child in children[current]:
                in_degree[child] -= 1  # 부모 하나를 방금 처리했으니 카운터를 깎는다
                # 0 이 되면 모든 부모가 먼저 나왔다는 뜻이니 이제 꺼내도 안전하다
                # 머지 커밋은 부모가 2개라 둘 다 나올 때까지 여기 못 들어온다
                if in_degree[child] == 0:
                    queue.append(child)

        # 순환이 있으면 서로를 기다리느라 진입차수가 0 이 되는 커밋이 없어서
        # 큐가 먼저 비어버린다. 그래서 개수만 비교해도 순환을 잡아낼 수 있다
        if len(result) != len(self.commits):
            raise ValueError("커밋 그래프에 순환이 있어서 위상 정렬을 할 수 없어요")

        return result

    def ancestors(self, commit_hash):

        if commit_hash not in self.commits:
            raise ValueError(f"{commit_hash} 커밋은 존재하지 않아요")

        # 부모 방향으로만 가는 BFS. 방향이 한쪽이라 DAG 가 유지되고 언젠가 최초 커밋에서 멈춘다
        visited = set()   # 여기서는 같은 커밋을 두 번 담지 않기 위한 중복 제거용
        queue = deque([commit_hash])
        result = []

        while queue:
            current = queue.popleft()
            for parent in self.commits[current].parents:
                if parent not in visited:
                    visited.add(parent)
                    result.append(parent)
                    queue.append(parent)

        return result

    def build_graph(self):
        graph = {}

        for hash in self.commits:
            graph[hash] = []

        for hash, commit in self.commits.items():
            for parent in commit.parents:
                graph[hash].append(parent) #자식 -> 부모
                graph[parent].append(hash)  #부모 -> 자식 <- D acylic G 이지만 순환이 생김
        return graph

    def path(self, hash_s, hash_e):

        if hash_s not in self.commits:
            raise ValueError(f"{hash_s} 커밋은 존재하지 않아요")
        if hash_e not in self.commits:
            raise ValueError(f"{hash_e} 커밋은 존재하지 않아요")

        # 갈라진 두 커밋을 이으려면 부모로 올라갔다가 자식으로 내려와야 하므로 무향 그래프를 쓴다
        graph = self.build_graph()

        queue = deque()
        queue.append(hash_s)

        visited = {hash_s: None} # 순환구조에서 해쉬 s를 방문했는지 확인하고, 경로를 추적하기 위해 부모 노드를 저장

        while queue:
            current = queue.popleft()   #앞에꺼 꺼내면서 제거 append 는 뒤에 넣는 거, popleft 는 앞에서 꺼내는 거 반대로 팝 쓰면 스택이 되고 dfs가 됨
            if current == hash_e:
                break

            for neighbor in graph[current]:
                # BFS 는 가까운 것부터 퍼지므로 처음 도달한 길이 곧 최단 경로다
                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.append(neighbor)

        if hash_e not in visited:
            raise ValueError(f"{hash_s} 와 {hash_e} 사이에는 경로가 없어요")

        # 도착점부터 저장해 둔 부모를 타고 거슬러 올라가며 경로를 복원한다
        path = []
        node = hash_e
        while node is not None:
            path.append(node)
            node = visited[node]

        # 거꾸로 쌓였으니 뒤집어서 시작 -> 도착 순서로 만든다
        path.reverse()
        return path

    def diff(self, file1, file2):
        pass

    def help(self):
        print("사용 가능한 명령어들:")
        print("INIT <user_name> : 저장소 초기화")
        print("COMMIT <message> : 커밋 생성")
        print("BRANCH <branch_name> : 브랜치 생성")
        print("SWITCH <branch_name> : 브랜치 변경")
        print("STATUS : 현재 상태 확인")
        print("LOG : 모든 커밋을 위상 정렬(부모 -> 자식) 순서로 출력, 브랜치가 걸린 커밋은 꼬리표 표시")
        print("LOG --sort-by=date : 작성 시간 순으로 정렬해서 출력")
        print("LOG --sort-by=author : 작성자 이름 순으로 정렬해서 출력")
        print("SEARCH <keyword> : 키워드 검색")
        print("SEARCH --author=<name> : 작성자로 검색")
        print("PATH <commit1> <commit2> : 두 커밋 사이의 최단 경로 탐색")
        print("ANCESTORS <commit_hash> : 해당 커밋의 모든 조상 출력")
        print("HELP : 도움말 보기")
