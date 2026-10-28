from solvers.base_solver import BaseSolver


MAX_DEPTH = 50


class IDSSolver(BaseSolver):
    def __init__(self, board, time_limit=None, node_limit=None, max_depth=MAX_DEPTH):
        super().__init__(board, time_limit, node_limit)
        self.max_depth = max_depth

    def _search(self):
        start = self.board.get_initial_state()
        if self.board.is_goal(start):
            return []
        for limit in range(self.max_depth + 1):
            solution, cutoff = self._dls(start, 0, limit, [], {start}, {})
            if solution is not None:
                return solution
            if not cutoff:
                return None
        self.status = "DEPTH_LIMIT"
        return None

    def _dls(self, state, depth, limit, path, on_path, best_depth):
        self._check_time()
        if self.board.is_goal(state):
            return list(path), False
        if best_depth.get(state, float("inf")) <= depth:
            return None, False
        if depth == limit:
            cutoff = any(next_state not in on_path
                         for _, next_state in self._successors(state))
            return None, cutoff
        best_depth[state] = depth
        cutoff = False
        for action, next_state in self._successors(state):
            if next_state in on_path:
                continue
            path.append(action)
            on_path.add(next_state)
            solution, child_cutoff = self._dls(
                next_state, depth + 1, limit, path, on_path, best_depth
            )
            on_path.remove(next_state)
            path.pop()
            if solution is not None:
                return solution, False
            cutoff = cutoff or child_cutoff
        return None, cutoff
