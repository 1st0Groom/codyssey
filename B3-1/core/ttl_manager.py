# TTL(Time to Live) 타이머 관리자
import time
from data_structures.min_heap import MinHeap
from data_structures.hash_map import HashMap

class TTLManager:
    def __init__(self):
        self.heap = MinHeap()
        self.ttl_map = HashMap() # 이 키가 정확히 몇 초에 죽는지 기록하는 장부.

    # 1. 수명 설정(expire) 
    # 키는 수명을 설정할 데이터 식별자
    # 세컨드는 데이터 유지될 시간
    # return 1을 하는 이유는 실제로 레디스에서 익스파이어 
    # 명령어를 실행하면 만료시간 갱신 성공하면 1 반환하고 실패하면 0 반환함.
    def expire(self, key, seconds):
        if seconds <= 0:
            return 1

        # time.time() 은 1970년부터 지금까지 흘러간 시간을 초로 반환하고 
        # 여기에 우리가 넣은 seconds를 더해서 변수를 지정해줌
        expire_at = time.time() + seconds

        # 힙에 이 시간에 울리라고 넣어둠 
        self.heap.push((expire_at, key)) # (시간 , 키) 를 튜플로 넣으면 시간 순으로 정렬함 (push 함수)
        # 정확한 시간 장부에도 씀
        self.ttl_map.put(key, expire_at) # 장부의 키에 만료시간을 기록해 둠(hash map 클래스에 put 함수 사용)
        return 1

    # 2. 남은 수명 확인 (ttl)
    def ttl(self, key):
        # 만약에 장부에 키가 없다면 -1 반환 (만료된거니까)(contains 함수 사용(있는지 확인하는 함수))
        if not self.ttl_map.contains(key): 
            return -1

        # get 함수 사용해서 데이터를 조회하여 만료 시간(시간)을 가져와 변수에 저장
        expire_at = self.ttl_map.get(key)
        now = time.time()

        # 이미 만료 시간이 지났다면?
        if now >= expire_at:
            return -2

        # 지난 거 아니면 남은 시간 정수 계산해서 반환
        return int(expire_at - now)

    # 3. 만료된 애들 싹 다 청소하기 (청소부)
    def clear_expired(self):
        expired_keys = []
        now = time.time()

        # 힙의 맨 꼭데기 (가장 빨리 죽는애)를 꺼내서 확인
        while self.heap.size() > 0:
            top_expire_at, top_key = self.heap.peek()

            # 만약 제일 빨리 죽을 애가 안 죽었다면 브렠
            if top_expire_at > now:
                break

            # 만료시간이 지났다면 힙에서 뽑음
            _, expired_key = self.heap.pop()

            # 예전에 덮어쓰기 돼서 장부(ttl_map)에 시간이랑 다를 수 있으니
            # 한번 더 확인
            if self.ttl_map.contains(expired_key):
                real_expire_at = self.ttl_map.get(expired_key)
                if now >= real_expire_at:
                    # 진짜 죽은 게 맞다면 삭제 명단에 추가
                    expired_keys.append(expired_key)
                    # 장부에서 삭제
                    self.ttl_map.remove(expired_key)
        # 메인 코드에게 얘네 죽었으니까 메인 저장소에서도 지우라고 알려줌
        return expired_keys 





















