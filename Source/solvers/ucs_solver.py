from solvers.base_solver import BaseSolver
import heapq
from core.state import Orientation
from solvers.search_utils import get_step_cost
class UCSSolver(BaseSolver):


    def _search(self):
        start_state = self.board.get_initial_state()
        if self.board.is_goal(start_state):
            return []
        
        frontier = [(0, start_state, [])]
        visited = set()

        while frontier:
            current_cost, current_state, path = heapq.heappop(frontier)
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
                    new_cost = current_cost + step_cost
                    
                    heapq.heappush(frontier, (new_cost, next_state, path + [action]))

        return None


