# 최소 힙 : 부모는 무조건 자식보다 숫자가 작거나 같아야 한다, 이 법칙을 지키며 데이터를 넣으면 제일 작은 숫자는 무조건 맨 꼭대기에 오르게 됨
# 수만 개의 키에 각기 다른 만료 시간이 적혀있을 때 누가 제일 먼저 묵는지를 찾고 싶으면 전체를 다 뒤질 필요 없이 맨 꼭대기만 확인하면 됨.

class MinHeap:
    # 힙은 단순한 파이썬 리스트로 구현함.
    def __init__(self):
        self.heap = []

    def size(self):
        # len으로 힙 리스트의 개수를 반환. 힙에 데이터가 몇 개 있는지.
        return len(self.heap)
    
    def peek(self):
        # 리스트가 비어있으면 None 반환. 
        if not self.heap:
            return None
        # 맨 꼭대기( 가장 작은 값(인덱스 0 ) ) 반환하기 (빼진 않음.)
        return self.heap[0]

# 1. 데이터 삽입 (PUSH)
    def push(self,item):
        # 맨 뒤에 일단 넣음.
        self.heap.append(item)
        # 방금 넣은 데이터를 조건에 맞게 위로 끌어올림.
        self._heapify_up(len(self.heap) - 1)

# 2. 최솟값 제거(POP)
    def pop(self):
        # 1. 리스트 비어있으면 None 반환
        if not self.heap:
            return None
        
        # 2. 1개만 있으면 바로 뺌
        if len(self.heap) == 1:
            return self.heap.pop()
        
        # 맨 꼭대기 루트 값(인덱스 0)을 따로 저장함
        root = self.heap[0]
        
        # 힙의 맨 뒤에 있던 놈을 맨 꼭대기로 데려와.
        self.heap[0] = self.heap.pop()

        # 0번부터 아래로 끌어내리기
        self._heapify_down(0)

        return root

# 3. 밑에서 위로 끌어올리기 (힙파이 업)
    def _heapify_up(self, index):
        # 내 부모가 몇 번인지 수학 공식으로 찾기.
        parent_idx = (index - 1) // 2

        # 내가 루트값이 아니고 내 값이 부모 값보다 작다면
        if index > 0 and self.heap[index] < self.heap[parent_idx]:
            # 부모와 나의 자리를 바꿈
            self.heap[index], self.heap[parent_idx] = self.heap[parent_idx], self.heap[index]
            # 그리고 바뀐 위치에서 또 위로 올라갈 수 있는지 재귀호출
            self._heapify_up(parent_idx)

# 4. 위에서 아래로 끌어내리기 (힙파이 다운)
    def _heapify_down(self, index):
        smallest = index # 일단 현재 위치를 가장 작다고 가정
        left_idx = 2 * index + 1    # 왼쪽 자식 번호
        right_idx = 2 * index + 2   # 오른쪽 자식 번호
        
        # 4-1 왼쪽 자식이 존재하고, 나보다 왼쪽 자식이 더 작다면
        if left_idx < len(self.heap) and self.heap[left_idx] < self.heap[smallest]:
            smallest = left_idx
        
        # 4-2 오른쪽 자식이 존재하고, 나보다 오른쪽 자식이 더 작다면
        if right_idx < len(self.heap) and self.heap[right_idx] < self.heap[smallest]:
            smallest = right_idx

        # 4-3 나보다 작은 자식이 발견되었다면 (자리를 바꿔야 함)
        if smallest != index:
            # 제일 작은 자식과 내 자리를 바꿉니다.

            self.heap[index], self.heap[smallest] = self.heap[smallest], self.heap[index]
            # 그리고 바뀐 위치에서 또 아래로 내려갈 수 있는지 재귀 호출
            self._heapify_down(smallest)
    
    

