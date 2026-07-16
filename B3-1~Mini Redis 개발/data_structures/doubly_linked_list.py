# 1. 기차 칸 1개 (Node) 설계도
class Node:
    def __init__(self, key=None, value=None):
        self.key = key       # 손님의 이름 (LRU 꼬리 자를 때 누구인지 알아야 하니까)
        self.value = value   # 손님의 짐 (실제 데이터)
        self.prev = None     # 앞쪽 연결 고리
        self.next = None     # 뒤쪽 연결 고리

# 2. 전체 기차 (이중 연결 리스트) 설계도
class DoublyLinkedList:
    def __init__(self):
        # 기차가 처음 만들어지면, 가짜 기관차(head)와 꼬리칸(tail)을 만들고 둘을 연결합니다.
        self.head = Node()
        self.tail = Node()
        
        # 기관차의 뒤쪽 고리를 꼬리칸에 걸고, 꼬리칸의 앞쪽 고리를 기관차에 겁니다.
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0 # 기차에 탄 손님 수 (노드 개수)

    # 1. 맨 앞에 노드를 추가 (기관차 바로 뒤에 새 칸 끼워넣기)
    def insert_front(self, node):
        # 1-1. 기관차의 원래 뒤에 있던 칸을 임시(temp)로 잡아둡니다.
        temp = self.head.next
        
        # 1-2. 기관차의 다음 칸을 '새 칸(node)'으로 지정!
        self.head.next = node
        node.prev = self.head  # 새 칸의 앞쪽은 기관차!
        
        # 1-3. 새 칸의 다음 칸을 아까 잡아둔 임시 칸(temp)으로 지정!
        node.next = temp
        temp.prev = node       # 임시 칸의 앞쪽은 새 칸!
        
        self.size += 1

    # 2. 맨 뒤에 노드를 추가 (꼬리칸 바로 앞에 새 칸 끼워넣기)
    def insert_back(self, node):
        # 2-1. 꼬리칸의 원래 앞에 있던 칸을 임시(temp)로 잡아둡니다.
        temp = self.tail.prev
        
        # 2-2. 꼬리칸의 앞칸을 '새 칸(node)'으로 지정!
        self.tail.prev = node
        node.next = self.tail  # 새 칸의 뒤쪽은 꼬리칸!
        
        # 2-3. 임시 칸(temp)의 다음 칸을 새 칸으로 지정!
        temp.next = node
        node.prev = temp       # 새 칸의 앞쪽은 임시 칸!
        
        self.size += 1

    # 3. 특정 노드 삭제 (중간에 있는 기차 칸 쏙 빼기)
    def remove_node(self, node):
        # 3-1. 내 앞칸과 내 뒷칸이 서로 직접 연결하게 만듭니다.
        prev_node = node.prev
        next_node = node.next
        
        prev_node.next = next_node
        next_node.prev = prev_node
        
        self.size -= 1

    # 4. 맨 앞으로 이동 (캐시 적중! 최근에 썼으니 맨 앞으로)
    def move_to_front(self, node):
        self.remove_node(node)   # 일단 기차에서 쏙 빼내고
        self.insert_front(node)  # 다시 기관차 바로 뒤(맨 앞)에 꽂아 넣습니다.

    # 5. 맨 앞 노드 삭제 (기관차 바로 뒤칸 빼기)
    def remove_front(self):
        # 만약 기관차 바로 다음이 꼬리칸이면? (손님이 없다는 뜻) -> 무시!
        if self.head.next == self.tail:
            return None
            
        first_node = self.head.next  # 첫 번째 칸을 찾아서
        self.remove_node(first_node) # 쏙 빼냅니다.
        return first_node            # 빼낸 칸을 반환 (누굴 뺐는지 알려주기)

    # 6. 맨 뒤 노드 삭제 (메모리 꽉 찼을 때, 가장 오래된 놈 버리기)
    def remove_back(self):
        # 만약 꼬리칸 바로 앞이 기관차면? (손님이 없다는 뜻) -> 무시!
        if self.tail.prev == self.head:
            return None
            
        lru_node = self.tail.prev    # 꼬리칸 바로 앞칸(가장 오래된 칸)을 찾아서
        self.remove_node(lru_node)   # 쏙 빼냅니다.
        return lru_node              # 빼낸 칸을 반환 (해시맵에서도 지워야 하니까!)