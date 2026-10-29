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
    def __init__(self, board):
        self.board = board

    def __call__(self, state: State) -> int:
        goal_r, goal_c = self.board.goal_pos
        max_dist = 0
        for r, c in state.get_occupied_cells():
            dist = abs(r - goal_r) + abs(c - goal_c)
            if dist > max_dist:
                max_dist = dist
        return max_dist * 5 / 2.0