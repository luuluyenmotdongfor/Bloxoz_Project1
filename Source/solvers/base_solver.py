import time
import tracemalloc
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.board import Board

class BaseSolver(ABC):
    def __init__(self, board: Board, time_limit=30, node_limit=500000):
        self.board = board
        self.expanded_nodes = 0
        self.time_limit = time_limit
        self.node_limit = node_limit
        self.start_time = 0
        self.status = "UNSOLVABLE"

    def solve(self) -> Dict[str, Any]:
        """
        Hàm chuẩn gọi từ GUI hoặc từ script Benchmark.
        Tự động đo Search Time và Peak Memory Usage (KiB).
        """
        self.expanded_nodes = 0
        self.status = "UNSOLVABLE"
        tracemalloc.start()
        start_time = time.perf_counter()
        self.start_time = start_time
        try:
            actions = self._search()
        finally:
            end_time = time.perf_counter()
            _, peak_memory_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        if self.time_limit is not None and end_time - start_time >= self.time_limit:
            self.status = "TIME_LIMIT"
            actions = None
        elif actions is not None:
            self.status = "OK"

        return {
            "status": self.status,
            "solved": actions is not None,
            "actions": actions if actions is not None else [],
            "solution_length": len(actions) if actions is not None else 0,
            "expanded_nodes": self.expanded_nodes,
            "search_time_sec": round(end_time - start_time, 6),
            "peak_memory_kb": round(peak_memory_bytes / 1024, 2)
        }

    def _limit_reached(self):
        if self.time_limit is not None:
            if time.perf_counter() - self.start_time >= self.time_limit:
                self.status = "TIME_LIMIT"
                return True
        if self.node_limit is not None and self.expanded_nodes >= self.node_limit:
            self.status = "NODE_LIMIT"
            return True
        return False

    @abstractmethod
    def _search(self) -> Optional[List[str]]:
        """
        Các class con (BFS, DFS, UCS, A*) cài đặt thuật toán tại đây.
        Mỗi lần gọi board.get_successors để mở rộng trạng thái, nhớ gọi:
            self.expanded_nodes += 1
        Trả về danh sách các bước đi (VD: ['RIGHT', 'DOWN', ...]) hoặc None nếu vô nghiệm.
        """
        pass