from solvers.base_solver import BaseSolver
import heapq
from solvers.search_utils import Heuristic, get_step_cost
class AStarSolver(BaseSolver):

    def __init__(self, board, time_limit=30, node_limit=500000):
        super().__init__(board, time_limit, node_limit)
        self.heuristic = Heuristic(self.board)

    def _search(self):
        start_state = self.board.get_initial_state()
        if self.board.is_goal(start_state):
            return []

        start_g = 0
        start_h = self.heuristic(start_state)
        start_f = start_g + start_h
        frontier = [(start_f, start_g, start_state, [])]
        visited = set()

        while frontier:
            current_f, current_g, current_state, path = heapq.heappop(frontier)
            if current_state in visited:
                continue
            visited.add(current_state)

            if self.board.is_goal(current_state):
                return path
            if self._limit_reached():
                return None
            self.expanded_nodes += 1
            successors = self.board.get_successors(current_state)

            for action, next_state in successors:
                if next_state not in visited:
                    # Tính chi phí bước đi và tổng chi phí mới
                    step_cost = get_step_cost(self.board, next_state)
                    new_g = current_g + step_cost

                    new_h = self.heuristic(next_state)
                    new_f = new_g + new_h
                    
                    heapq.heappush(frontier, (new_f, new_g, next_state, path + [action]))

        return None

