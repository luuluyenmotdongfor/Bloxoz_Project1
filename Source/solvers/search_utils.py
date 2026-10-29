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
        predecessors = {}
        for source, switch in board.switches.items():
            if switch["type"] == "split":
                for target in switch["teleport_to"]:
                    predecessors.setdefault(tuple(target), []).append(source)
        goal = board.goal_pos
        self.distance = {goal: 0}
        queue = [(0, goal)]
        while queue:
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

# Các hàm dưới đang thử cải thiện Heuristic cho Mahattan chưa qua chạy thử đang đợi hồi tokens để test thử
    def get_mahattan_distance(self, p1, p2):
        " Tính khoảng cách mahattan tới đích"
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    
    def merge_to_goal(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        dist_between = self.get_mahattan_distance(pos1, pos2)
        h_meet = max(0, (dist_between - 1) // 2)
        target = self.board.goal_pos
        h_target = max(self.get_mahattan_distance(pos1, target), self.get_mahattan_distance(pos2, target))
        return h_meet + h_target

    def mahattan_heuristic(self):
        self.switch_destinations = {}
        for source, switch in self.board.switches.items():
            if switch["type"] == "split":
            # Chuyển đổi các điểm đích thành tuple để đồng bộ cấu trúc dữ liệu nếu cần
                self.switch_destinations[source] = [tuple(target) for target in switch["teleport_to"]]
        self.switch_heuristic = {}
        for source in self.switch_destinations.keys():
            pos1, pos2 = self.switch_destinations[source][0], self.switch_destinations[source][1]
            self.switch_heuristic[source] = self.merge_to_goal(pos1, pos2)
        
    def get_heuristic(self, state):
        goal_r, goal_c = self.board.goal_pos
        r, c = state.get_occupied_cells()
        if state.orientation == 3:
            cells = state.get_occupied_cells()

            r1, c1 = cells[0]
            distance1 = abs(r1 - goal_r) + abs(c1 - goal_c)
            r2, c2 = cells[1]
            distance2 = abs(r2 - goal_r) + abs(c2 - goal_c)
            return min(distance1, distance2) / 2.0
            
        min_heu = abs(r - goal_r) + abs(c - goal_c)
        for source, cost in self.switch_heuristic.items():
            to_switch = self.get_mahattan_distance((r,c), source)
            if to_switch + cost < min_heu:
                min_heu = to_switch + cost
        return min_heu
    