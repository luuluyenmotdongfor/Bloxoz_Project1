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
        self.distances = {}
        self._precompute()

    def _precompute(self):
        goal_r, goal_c = self.board.goal_pos
        pq = [(0, goal_r, goal_c)]
        self.distances[(goal_r, goal_c)] = 0
        teleport_edges = {}
        for (sr, sc), switch in self.board.switches.items():
            if switch["type"] == "split":
                targets = switch.get("targets", [])
                for tr, tc in targets:
                    teleport_edges.setdefault((tr, tc), []).append((sr, sc))

        while pq:
            dist, r, c = heapq.heappop(pq)
            
            if dist > self.distances.get((r, c), float('inf')):
                continue
                
            if (r, c) in teleport_edges:
                for sr, sc in teleport_edges[(r, c)]:
                    new_dist = dist + 20 # Cộng thêm 20 khớp với hình phạt Split
                    if new_dist < self.distances.get((sr, sc), float('inf')):
                        self.distances[(sr, sc)] = new_dist
                        heapq.heappush(pq, (new_dist, sr, sc))

            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.board.rows and 0 <= nc < self.board.cols:
                    if self.board.grid[nr][nc] != 0:
                        new_dist = dist + 5 # 1 bước đi = 10 units
                        if new_dist < self.distances.get((nr, nc), float('inf')):
                            self.distances[(nr, nc)] = new_dist
                            heapq.heappush(pq, (new_dist, nr, nc))

    def __call__(self, state: State) -> int:

        return min((self.distances.get((r, c), float('inf')) 
                    for r, c in state.get_occupied_cells()), default=float('inf'))