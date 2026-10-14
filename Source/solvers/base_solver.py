import time
import tracemalloc
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from core.board import Board

class BaseSolver(ABC):
    def __init__(self, board: Board):
        self.board = board
        self.expanded_nodes = 0

    def solve(self) -> Dict[str, Any]:
        """
        Hàm chuẩn gọi từ GUI hoặc từ script Benchmark.
        Tự động đo Search Time và Peak Memory Usage (KB).
        """
        self.expanded_nodes = 0
        tracemalloc.start()
        start_time = time.perf_counter()

        actions = self._search()

        end_time = time.perf_counter()
        _, peak_memory_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            "solved": actions is not None,
            "actions": actions if actions is not None else [],
            "solution_length": len(actions) if actions is not None else 0,
            "expanded_nodes": self.expanded_nodes,
            "search_time_sec": round(end_time - start_time, 6),
            "peak_memory_kb": round(peak_memory_bytes / 1024, 2)
        }

    @abstractmethod
    def _search(self) -> Optional[List[str]]:
        """
        Các class con (BFS, DFS, UCS, A*) cài đặt thuật toán tại đây.
        Mỗi khi lấy 1 node ra khỏi hàng đợi (frontier) để mở rộng, nhớ gọi:
            self.expanded_nodes += 1
        Trả về danh sách các bước đi (VD: ['RIGHT', 'DOWN', ...]) hoặc None nếu vô nghiệm.
        """
        pass