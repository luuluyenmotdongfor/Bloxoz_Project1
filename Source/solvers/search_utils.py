from core.state import Orientation
from core.state import State
import heapq
def get_step_cost(board, next_state):
    state_cost = 0
    block_cost = 10

    if next_state.orientation == 3:
        state_cost += 20
    closed_bridges = next_state.bridges_mask.count(False)
    state_cost += closed_bridges * 1
    for r, c in next_state.get_occupied_cells():
        if board.grid[r][c] == 2:
            block_cost += 20
            break
    return state_cost + block_cost

class Heuristic:
    def __init__(self, board, check_time=lambda: None):
        self.board = board
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

        

    def __call__(self, state: State) -> int:
        # goal_r, goal_c = self.board.goal_pos
        # max_dist = 0
        # for r, c in state.get_occupied_cells():
        #     dist = abs(r - goal_r) + abs(c - goal_c)
        #     if dist > max_dist:
        #         max_dist = dist
        # #return max_dist * 5 / 2.0
        return min(self.distance[cell] for cell in state.get_occupied_cells())