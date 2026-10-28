import heapq
from core.state import Orientation


def reconstruct_path(parents, state):
    actions = []
    while parents[state] is not None:
        state, action = parents[state]
        actions.append(action)
    return actions[::-1]


def step_cost_units(board, state):
    fragile = any(board.grid[r][c] == 2 for r, c in state.get_occupied_cells())
    # Ten integer units represent one cost point.
    return (10 + 20 * fragile + 20 * (state.orientation == Orientation.SPLIT)
            + state.bridges_mask.count(False))


class RelaxedHeuristic:
    def __init__(self, board, check_time=lambda: None):
        predecessors = {}
        for source, switch in board.switches.items():
            if switch["type"] == "split":
                for target in switch["teleport_to"]:
                    predecessors.setdefault(tuple(target), []).append(source)
        goal = board.goal_pos
        self.distance = {goal: 0}
        queue = [(0, goal)]
        while queue:
            check_time()
            distance, cell = heapq.heappop(queue)
            if distance != self.distance[cell]:
                continue
            r, c = cell
            edges = [((r - 1, c), 5), ((r + 1, c), 5),
                     ((r, c - 1), 5), ((r, c + 1), 5)]
            edges.extend((source, 0) for source in predecessors.get(cell, []))
            for previous, weight in edges:
                pr, pc = previous
                if 0 <= pr < board.rows and 0 <= pc < board.cols:
                    candidate = distance + weight
                    if candidate < self.distance.get(previous, float("inf")):
                        self.distance[previous] = candidate
                        heapq.heappush(queue, (candidate, previous))

    def __call__(self, state):
        return min(self.distance[cell] for cell in state.get_occupied_cells())
