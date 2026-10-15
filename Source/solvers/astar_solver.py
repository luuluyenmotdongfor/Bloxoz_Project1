from solvers.base_solver import BaseSolver
import heapq
class AStarSolver(BaseSolver):


    def _get_heuristic(self, state):
        goal_r, goal_c = self.board.goal_pos
        cells = state.get_occupied_cells()

        r1, c1 = cells[0]
        distance1 = abs(r1 - goal_r) + abs(c1 - goal_c)
        
        if len(cells) > 1:
            r2, c2 = cells[1]
            distance2 = abs(r2 - goal_r) + abs(c2 - goal_c)
            return min(distance1, distance2) / 2.0
            
        return distance1 / 2.0

    def _search(self):
        start_state = self.board.get_initial_state()
        if self.board.is_goal(start_state):
            return []

        start_g = 0
        start_h = self._get_heuristic(start_state)
        start_f = start_g + start_h
        frontier = [(start_f, start_g, start_state, [])]
        visited = set()

        while frontier:
            current_f, current_g, current_state, path = heapq.heappop(frontier)
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
                    new_g = current_g + step_cost

                    new_h = self._get_heuristic(next_state)
                    new_f = new_g + new_h
                    
                    heapq.heappush(frontier, (new_f, new_g, next_state, path + [action]))

        return None


    def _get_step_cost(self, action, next_state):
        return 1