from solvers.base_solver import BaseSolver
import heapq
from core.state import Orientation
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
            self.expanded_nodes += 1

            if self.board.is_goal(current_state):
                return path

            successors = self.board.get_successors(current_state)

            for action, next_state in successors:
                if next_state not in visited:
                    # Tính chi phí bước đi và tổng chi phí mới
                    step_cost = self._get_step_cost(action, next_state)
                    new_cost = current_cost + step_cost
                    
                    heapq.heappush(frontier, (new_cost, next_state, path + [action]))

        return None


    def _get_step_cost(self, action, next_state):
        state_cost = 1
        block_cost = 0

        if next_state.orientation == 3:
            state_cost += 2
        if not all(next_state.bridges_mask): 
            state_cost += 2
        for r, c in next_state.get_occupied_cells():
            if self.board.grid[r][c] == 2:
                block_cost += 4
                break
        return state_cost + block_cost