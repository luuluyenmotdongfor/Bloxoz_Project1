from solvers.base_solver import BaseSolver
class DFSSolver(BaseSolver):
    
    def _search(self):
        start_state = self.board.get_initial_state()
        if self.board.is_goal(start_state):
            return []

        frontier = [(start_state, [])]
        visited = {start_state}
        
        while frontier:
            cur_state, path = frontier.pop()

            if self.board.is_goal(cur_state):
                return path

            for action, next_state in self.board.get_successors(cur_state):
                if next_state not in visited:
                    visited.add(next_state)
                    new_path = path + [action]
                    frontier.append((next_state, new_path))
        return path