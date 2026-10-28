import time
import tracemalloc
from abc import ABC, abstractmethod


class SearchLimit(Exception):
    pass


class BaseSolver(ABC):
    def __init__(self, board, time_limit=None, node_limit=None):
        self.board = board
        self.time_limit = time_limit
        self.node_limit = node_limit
        self.expanded_nodes = 0
        self.status = "UNSOLVABLE"
        self._deadline = None

    def _check_time(self):
        if self._deadline is not None and time.perf_counter() >= self._deadline:
            raise SearchLimit("TIME_LIMIT")

    def _successors(self, state):
        self._check_time()
        if self.node_limit is not None and self.expanded_nodes >= self.node_limit:
            raise SearchLimit("NODE_LIMIT")
        self.expanded_nodes += 1
        return self.board.get_successors(state)

    def solve(self):
        self.expanded_nodes = 0
        self.status = "UNSOLVABLE"
        actions = None
        tracemalloc.start()
        start = time.perf_counter()
        self._deadline = start + self.time_limit if self.time_limit is not None else None
        try:
            if not self.board.is_valid_state(self.board.get_initial_state()):
                raise ValueError("Invalid initial state")
            actions = self._search()
            self._check_time()
            if actions is not None:
                self.status = "OK"
        except SearchLimit as exc:
            actions = None
            self.status = str(exc)
        finally:
            elapsed = time.perf_counter() - start
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            self._deadline = None
        return {
            "status": self.status,
            "solved": actions is not None,
            "actions": actions if actions is not None else [],
            "solution_length": len(actions) if actions is not None else 0,
            "expanded_nodes": self.expanded_nodes,
            "search_time_sec": elapsed,
            "peak_memory_kb": peak / 1024,
            "peak_memory_kib": peak / 1024,
        }

    @abstractmethod
    def _search(self):
        pass
