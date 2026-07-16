# 연결 리스트, 해시 맵, 힙을 사용하여 만든 레디스 저장소
# 1. 만료된 (TTL)데이터가 있는지 확인하고 알아서 청소
# 2. 데이터를 저장하거나 찾을 때, 이중 연결 리스트 순서를 바꿔 LRU(최근 사용)를 유지
# 3. 데이터가 들어올 때마다 메모리를 계산해서 
from data_structures.doubly_linked_list import Node, DoublyLinkedList
from data_structures.hash_map import HashMap
from core.ttl_manager import TTLManager

class MiniRedisStore:
    def __init__(self):
        # 1. 3개의 자료구조 알고리즘 부품 조립
        self.dll = DoublyLinkedList()   # LRU 순서 기록용 기차
        self.hash_map = HashMap()       # 검색용
        self.ttl_manager = TTLManager() # ttl 관리자 생성

        # 2. 메모리 관리 변수
        self.maxmemory = 0      # 0은 무제한이라는 뜻
        self.used_memory = 0    # 현재 사용 중인 메모리 총량
        self.evicted_keys = 0   # 메모리가 꽉 차서 쫒겨난 데이터 수

    # ---[내부 유틸리티 함수들]---

    # 메모리 사용량
    def _calc_memory_(self, key, value):
        # 요구사항 공식 : used_memory = sigma(len(utf8(key)) + len(utf8(value)))
        return len(str(key).encode('utf-8')) + len(str(value).encode('utf-8'))

    def _clean_up_expired(self):
        # 명령어 실행 전에 항상 만료된 데이터를 싹 치우는 역할 (게으른 삭제)
        expired_keys = self.ttl_manager.clear_expired() #ttl manager에 클리어 익스파이어드(청소부) 함수 실행
        for key in expired_keys:
            if self.hash_map.contains(key):     # 해쉬맵에 있는지 확인하는 함수 실행
                node = self.hash_map.get(key)   # 노드에 키 가져와서 저장
                self.dll.remove_node(node)      #연결 리스트에서 삭제
                self.hash_map.remove(key)       #해쉬맵에서 삭제
                self.used_memory -= self._calc_memory_(key, node.value) # 사용중인 메모리에서 변환

    def _evict_if_needed(self): # evict : 강제퇴출
        # 메모리 초과시 LRU (가장 오래된 놈) 퇴출 로직
        if self.maxmemory > 0:  # 만약에 맥스메모리가 0 보다 크면(즉 제한이 있으면)
            while self.used_memory > self.maxmemory: # 메모리가 맥스보다 클 때에
                lru_node = self.dll.remove_back() # 가장 오래된놈(제일 뒤에 있는놈)을 연결리스트에서 제거
                if lru_node:
                    self.hash_map.remove(lru_node.key) # 해쉬맵에서 제거
                    # 현재 사용 중인 메모리 총량에 가장 오래된 노드의 사용량을 뺌
                    self.used_memory -= self._calc_memory_(lru_node.key, lru_node.value)
                    self.evicted_keys += 1 # 쫒겨난 데이터 수 1 증가

                    # 타임 투 라이브 타이머 관리자 안에 몇 초에 죽는지 기록하는 장부(해쉬맵)에 있는지 확인
                    if self.ttl_manager.ttl_map.contains(lru_node.key):
                        # 있다면 그 키를 장부에서 삭제 (가비지 컬렉터 작동)
                        self.ttl_manager.ttl_map.remove(lru_node.key)
    
    # --- 사용자 명령어 처리 ---
    # 1. 데이터 저장 SET
    def SET(self, key, value):
        self._clean_up_expired() # 실행 전 청소
        item_mem = self._calc_memory_(key,value)

        # 엣지 케이스: 들어올 데이터 하나가 전체 메모리보다 크면 저장 거부 (OOM)
        if self.maxmemory > 0 and item_mem > self.maxmemory:
            return "(error) OOM command not allowed when used_memory > 'maxmemory'."

        # 1. 이미 있는 키를 덮어쓸 때
        if self.hash_map.contains(key): # 만약 해쉬맵에 키가 있으면
            node = self.hash_map.get(key) # 노드에 키 가져와서 저장
            old_mem = self._calc_memory_(key, node.value) # 올드메모리 변수에 키에 저장한 메모리 사용량 저장

            node.value = value # 값 변경
            self.used_memory = self.used_memory + item_mem - old_mem # 사용중인 메모리 값에 - old_mem 하고 + item_mem 함 (즉 덮어쓰기 했으니 더하거나 뺀다)
            self.dll.move_to_front(node)    # 맨 앞으로 이동

            # 기존에 설정된 ttl 알람이 있었다면 초기화 해줌
            if self.ttl_manager.ttl_map.contains(key):
                self.ttl_manager.ttl_map.remove(key)
        
        # 2. 완전 새로운 키일 때
        else:
            new_node = Node(key, value)         # 새로운 노드 생성
            self.dll.insert_front(new_node)     # 연결 리스트 맨 앞에 추가
            self.hash_map.put(key, new_node)    # 해쉬맵에 키와 노드 추가
            self.used_memory += item_mem        # 사용중인 메모리에 추가

        # 3. 저장 후 메모리가 넘치면 퇴출
        self._evict_if_needed() 
        return "OK"

    # 2. 데이터 조회 get
    def GET(self, key) :
        self._clean_up_expired() # 실행 전 청소

        # 만약 해쉬맵에 키가 있으면
        if self.hash_map.contains(key):
            node = self.hash_map.get(key)
            self.dll.move_to_front(node)
            return f'"{node.value}"'
        # 키가 없으면 닐 리턴
        return "(nil)" # nil은 빈 값을 뜻함
    
    # 3. 데이터 삭제
    def DEL(self, key):
        self._clean_up_expired() # 실행 전 청소

        # 만약에 해쉬맵에 키가 있으면
        if self.hash_map.contains(key):
            node = self.hash_map.get(key)
            self.dll.remove_node(node) # 연결리스트에서 삭제
            self.hash_map.remove(key) # 해쉬맵에서 삭제
            self.used_memory -= self._calc_memory_(key, node.value) # 사용중인 메모리에서 삭제한 메모리 뺌

            # ttl 타임어에 혹시 키가 있다면 제거
            if self.ttl_manager.ttl_map.contains(key):
                self.ttl_manager.ttl_map.remove(key)
            return "(integer) 1"
        # 키가 없으면
        return "(integer) 0"

    
    # 4. 키 존재 확인
    def EXISTS(self, key):
        self._clean_up_expired() # 실행 전 청소
        # 해쉬맵에 키가 있으면 1 변환, 없으면 0 변환
        return "(integer) 1" if self.hash_map.contains(key) else "(integer) 0"
        
    # 5. 데이터베이스 사이즈 정보
    def DBSIZE(self):
        self._clean_up_expired() # 실행 전 청소
        return f"(integer) {self.hash_map.size}"

    # 6. 키 리스트 확인
    def KEYS(self):
        self._clean_up_expired()    # 실행 전 청소
        keys_list = self.hash_map.keys() # 해쉬맵에서 키 리스트 가져오기
        if not keys_list:   # 만약 키 리스트가 없으면
            return "(empty array)"       # 빈 배열 이라고 출력
        # 1. "key 1"
        #    "key 2" 형태로 예쁘게 출력
        result = []
        for i, k in enumerate(keys_list):
            result.append(f'{i+1},"{k}"')
        return "\n".join(result)
    
    # 7. 메모리 제한 설정
    def CONFIG_SET(self, param, value):
        # 만약 param 소문자가 maxmemory 면?
        if param.lower() == "maxmemory":
            try:
                val = int(value)
                # 만약 벨류가 0보다 작으면 벨류에러 출력
                if val < 0 :
                    raise ValueError
                self.maxmemory = val # max메모리 업데이트
                self._evict_if_needed() # 업데이트 후 퇴출 검사
                return "OK"
        
            except ValueError:
                # ValueError가 발생하면(정수가 아니거나 범위를 벗어나면)
                # 벨류가 정수가 아니거나 범위를 벗어났다.
                return "(error) ERR value is not an integer or out of range"
        return "(error) ERR unknown config parameter"

    # 메모리 정보 반환
    def INFO_memory(self):
        # 사용량 메모리랑, 최대 메모리, 쫒겨난 키 개수를 출력한다.
        return f"used_memory:{self.used_memory}\nmaxmemory:{self.maxmemory}\nevicted_keys:{self.evicted_keys}"

    # 키에 만료 시간 설정
    def EXPIRE(self, key, seconds):
        self._clean_up_expired() # 실행 전 청소
        # 만약에 키가 존재하지 않으면 0을 반환한다.
        if not self.hash_map.contains(key):
            return "(integer) 0"
        # 결과는 타임 투 매니저 의 익스파이어 메소드 안에서 나온다.
        result = self.ttl_manager.expire(key, seconds)
        # 만약에 주어진 세컨즈가 0보다 작으면
        if seconds <= 0:
            # 삭제를 해버린다.
            self.DEL(key)
        # 성공 여부를 반환
        return f"(integer) {result}" 
    
    # 키의 남은 시간을 반환
    def TTL(self,key):
        self._clean_up_expired()
        # 만약 키가 존재하지 않으면
        if not self.hash_map.contains(key):
            return "(integer) -2"
        # 잇으면 타임투매니저 에서 키값의 남은 시간을 반환
        return f"(integer) {self.ttl_manager.ttl(key)}"
        
    
        



    




