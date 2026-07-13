class HashNode:
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.next = None #체이닝용

class HashMap:
    def __init__(self, capacity=8):
        self.capacity = capacity    # 사물함 총 개수
        self.size = 0               # 현재 짐을 넣은 진짜 손님 수
        self.buckets = [None] * self.capacity   # 사물함 배열, 처음엔 다 비어있음(None)

    # 1. 해시 함수
    # 글자를 아스키코드를 이용하여 숫자로 변환 후 사물함 개수로 나눈 나머지를 구함.
    def _hash_function(self, key):
        hash_val = 0
        for char in str(key):
            hash_val += ord(char)
        return hash_val % self.capacity

    # 2. 데이터 저장 (Put)
    def put(self, key, value):
        # (손님 수/ 사물함 수) 가 0.75를 넘었을 때 사물함을 2배 늘림.
        if self.size / self.capacity > 0.75:
            self._resize()
        
        index = self._hash_function(key)
        current = self.buckets[index]
        
        # 2-1 사물함이 비었다면
        if current is None:
            self.buckets[index] = HashNode(key,value)
            self.size += 1
            return

        # 2-2 사물함에 누군가 이미 있다면? -> 체이닝: 연결리스트로 뒤에 붙인다.
        while current:
            if current.key == key:
                current.value = value
                return
            if current.next is None:
                current.next = HashNode(key, value)
                self.size += 1
                return
            current = current.next

        # 3. 데이터 조회 (GET)
    def get(self, key):
        index = self._hash_function(key)
        current = self.buckets[index]

        # 사물함에 매달린 줄을 차례대로 탐색
        while current:
            if current.key == key:
                return current.value
            current = current.next
        
        return None # 끝까지 찾았는데 없으면 None

    # 4. 데이터 삭제 (REMOVE)
    def remove(self, key):
        index = self._hash_function(key)
        current = self.buckets[index]
        prev = None

        while current:
            if current.key == key:
                # 맨 앞 사람이면?
                if prev is None:
                    self.buckets[index] = current.next
                # 중간에 낀 사람이면? 내 앞사람과 뒷사람을 다이렉트로 연결 (나를 왕따시킴)
                else:
                    prev.next = current.next
                self.size -= 1
                return
            prev = current
            current = current.next

    # 5. 있는지 확인 (CONTAINS)
    def contains(self, key):
        return self.get(key) is not None

    # 6. 모든 키 가져오기 (KEYS 명령어용)
    def keys(self):
        key_list = []
        # 모든 사물함을 돌면서 매달려 있는 키들을 다 모읍니다.
        for node in self.buckets:
            current = node
            while current:
                key_list.append(current.key)
                current = current.next
        return key_list

    # 7. 사물함 2배로 늘리기 (RESIZE)
    def _resize(self):
        old_buckets = self.buckets
        self.capacity *= 2  # 크기 2배 뻥튀기!
        self.buckets = [None] * self.capacity # 더 큰 새 사물함 배열 생성
        self.size = 0 # 짐을 다시 넣어야 하니 일단 0으로 초기화

        # 옛날 사물함에 있던 짐들을 꺼내서 새 사물함에 다시 PUT (Rehashing)
        for node in old_buckets:
            current = node
            while current:
                self.put(current.key, current.value)
                current = current.next