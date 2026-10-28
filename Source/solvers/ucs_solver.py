import heapq
from itertools import count
from solvers.base_solver import BaseSolver
from solvers.search_utils import reconstruct_path, step_cost_units


class UCSSolver(BaseSolver):
    def _search(self):
        start = self.board.get_initial_state()
        order = count()
        frontier = [(0, next(order), start)]
        best_g = {start: 0}
        parents = {start: None}
        while frontier:
            self._check_time()
            cost, _, state = heapq.heappop(frontier)
            if cost != best_g[state]:
                continue
            if self.board.is_goal(state):
                return reconstruct_path(parents, state)
            for action, next_state in self._successors(state):
                new_cost = cost + step_cost_units(self.board, next_state)
                if new_cost < best_g.get(next_state, float("inf")):
                    best_g[next_state] = new_cost
                    parents[next_state] = (state, action)
                    heapq.heappush(frontier, (new_cost, next(order), next_state))
        return None
