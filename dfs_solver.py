class DFSSolver(BaseSolver):
    
    def _search(self):
        start_state = self.board.get_initial_state()
        if self.board.is_goal(start_state):
            return []

        frontier = [(start_state, [])]
        visited = {start_state}
        
        curr_state, path = frontier.pop()
        def dfs(state):
            visited.add(state) 
            for action, next_state in self.board.get_successors(state):
                if next_state not in visited:
                    if self.board.is_goal(next_state):
                        return path + [action]
                    visited.add(next_state)
                    path += [action]
                    dfs(next_state)
        dfs(curr_state)
        return path