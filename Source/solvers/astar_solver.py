from solvers.base_solver import BaseSolver
import heapq
class AStarSolver(BaseSolver):


    def _get_heuristic(self, state):
        goal_r, goal_c = self.board.goal_pos
        cells = state.get_occupied_cells()

        r1, c1 = cells[0]
        distance1 = abs(r1 - goal_r) + abs(c1 - goal_c)
        distance = distance1
        
        if len(cells) > 1:
            r2, c2 = cells[1]
            distance2 = abs(r2 - goal_r) + abs(c2 - goal_c)
            distance = min(distance1, distance2)

        # Xem cổng Split như đích phụ để không ước lượng quá cao khi dịch chuyển.
        for (split_r, split_c), switch in self.board.switches.items():
            if switch["type"] == "split":
                for r, c in cells:
                    split_distance = abs(r - split_r) + abs(c - split_c)
                    distance = min(distance, split_distance)

        return distance / 2.0

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

            if self.board.is_goal(current_state):
                return path

            if self._limit_reached():
                return None
            self.expanded_nodes += 1
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
        state_cost = 0
        block_cost = 1

        if next_state.orientation == 3:
            state_cost += 2
        closed_bridges = next_state.bridges_mask.count(False)
        state_cost += closed_bridges * 0.1
        for r, c in next_state.get_occupied_cells():
            if self.board.grid[r][c] == 2:
                block_cost += 2
                break
        return state_cost + block_cost