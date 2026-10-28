from collections import deque
from solvers.base_solver import BaseSolver
from solvers.search_utils import reconstruct_path


class BFSSolver(BaseSolver):
    def _search(self):
        start = self.board.get_initial_state()
        if self.board.is_goal(start):
            return []
        frontier = deque([start])
        parents = {start: None}
        while frontier:
            self._check_time()
            state = frontier.popleft()
            for action, next_state in self._successors(state):
                if next_state in parents:
                    continue
                parents[next_state] = (state, action)
                if self.board.is_goal(next_state):
                    return reconstruct_path(parents, next_state)
                frontier.append(next_state)
        return None
