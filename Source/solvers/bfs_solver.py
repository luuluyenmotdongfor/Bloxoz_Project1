from collections import deque
from solvers.base_solver import BaseSolver

class BFSSolver(BaseSolver):
    def _search(self):
        start_state = self.board.get_initial_state()
        if self.board.is_goal(start_state):
            return []

        frontier = deque([(start_state, [])])
        visited = {start_state}

        while frontier:
            if self._limit_reached():
                return None
            current_state, path = frontier.popleft()
            self.expanded_nodes += 1

            for action, next_state in self.board.get_successors(current_state):
                if next_state not in visited:
                    if self.board.is_goal(next_state):
                        return path + [action]
                    visited.add(next_state)
                    frontier.append((next_state, path + [action]))
        return None