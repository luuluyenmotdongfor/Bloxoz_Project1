from solvers.base_solver import BaseSolver
from solvers.search_utils import reconstruct_path


class DFSSolver(BaseSolver):
    def _search(self):
        start = self.board.get_initial_state()
        frontier = [start]
        parents = {start: None}
        while frontier:
            self._check_time()
            state = frontier.pop()
            if self.board.is_goal(state):
                return reconstruct_path(parents, state)
            for action, next_state in self._successors(state):
                if next_state not in parents:
                    parents[next_state] = (state, action)
                    frontier.append(next_state)
        return None
