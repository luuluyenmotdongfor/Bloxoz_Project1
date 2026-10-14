import json
from typing import List, Tuple
from core.state import State, Orientation

ACTIONS = ["UP", "DOWN", "LEFT", "RIGHT"]
SPLIT_ACTIONS = ["UP", "DOWN", "LEFT", "RIGHT", "SWITCH_CUBE"]

class Board:
    def __init__(self, json_path: str):
        with open(json_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)

        self.name = data.get("name", "Unnamed Level")
        self.grid = data["grid"]
        self.rows = len(self.grid)
        self.cols = len(self.grid[0])
        self.start_pos = tuple(data["start"])
        self.goal_pos = tuple(data["goal"])

        # Sắp xếp tên cầu theo thứ tự bảng chữ cái để ánh xạ cố định vào bridges_mask
        bridges_data = data.get("bridges", {})
        self.bridge_ids = sorted(bridges_data.keys())
        self.bridge_id_to_idx = {b_id: i for i, b_id in enumerate(self.bridge_ids)}

        # Map tọa độ ô cầu -> chỉ số trong bridges_mask
        self.cell_to_bridge_idx = {}
        initial_mask = []
        for idx, b_id in enumerate(self.bridge_ids):
            b_info = bridges_data[b_id]
            initial_mask.append(bool(b_info["initial_state"]))
            for r, c in b_info["cells"]:
                self.cell_to_bridge_idx[(r, c)] = idx
        self.initial_bridges_mask = tuple(initial_mask)

        # Lưu thông tin công tắc theo tọa độ (r, c)
        self.switches = {}
        for sw in data.get("switches", []):
            self.switches[tuple(sw["pos"])] = sw

    def get_initial_state(self) -> State:
        """Khối bắt đầu ở trạng thái đứng thẳng trên ô xuất phát."""
        return State(
            r=self.start_pos[0],
            c=self.start_pos[1],
            orientation=Orientation.STANDING,
            bridges_mask=self.initial_bridges_mask
        )

    def is_goal(self, state: State) -> bool:
        """Thắng khi khối nguyên đứng thẳng đúng trên lỗ đích."""
        return (
            state.orientation == Orientation.STANDING
            and (state.r, state.c) == self.goal_pos
        )

    def is_valid_state(self, state: State) -> bool:
        """Kiểm tra khối có bị rơi ra ngoài, rơi xuống Void, cầu đang đóng, hoặc làm vỡ Fragile tile không."""
        cells = state.get_occupied_cells()
        for r, c in cells:
            # 1. Rơi ra ngoài biên bản đồ
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                return False
            # 2. Nếu ô này là một cây cầu, kiểm tra cầu đang đóng hay mở
            if (r, c) in self.cell_to_bridge_idx:
                b_idx = self.cell_to_bridge_idx[(r, c)]
                if not state.bridges_mask[b_idx]:
                    return False  # Cầu đang đóng -> coi như ô trống (Void)
            else:
                # Không phải cầu mở mà grid == 0 -> rơi xuống Void
                if self.grid[r][c] == 0:
                    return False

        # 3. Kiểm tra ô dễ vỡ (Fragile tile - mã 2): vỡ nếu khối đứng thẳng đè toàn bộ trọng lượng lên
        if state.orientation == Orientation.STANDING:
            r, c = state.r, state.c
            if self.grid[r][c] == 2:
                return False

        return True

    def get_successors(self, state: State) -> List[Tuple[str, State]]:
        """Trả về danh sách các cặp (action, next_state) hợp lệ từ trạng thái hiện tại."""
        successors = []
        possible_actions = SPLIT_ACTIONS if state.orientation == Orientation.SPLIT else ACTIONS

        for action in possible_actions:
            next_state = self._apply_move(state, action)
            if next_state is not None and self.is_valid_state(next_state):
                # Sau khi lăn hợp lệ, kiểm tra kích hoạt công tắc (Switches)
                final_state = self._trigger_switches(state, next_state, action)
                if self.is_valid_state(final_state):
                    successors.append((action, final_state))
        return successors

    def _apply_move(self, s: State, action: str) -> State:
        """Bảng chuyển trạng thái (Orientation Transition Table) chuẩn."""
        r, c, ori, mask = s.r, s.c, s.orientation, s.bridges_mask

        # TRƯỜNG HỢP 1: Khối đang bị tách làm 2 khối đơn 1x1x1
        if ori == Orientation.SPLIT:
            if action == "SWITCH_CUBE":
                return State(r, c, Orientation.SPLIT, mask, s.r2, s.c2, 1 - s.active_cube)

            dr, dc = {"UP": (-1, 0), "DOWN": (1, 0), "LEFT": (0, -1), "RIGHT": (0, 1)}[action]
            nr1, nc1, nr2, nc2 = r, c, s.r2, s.c2
            if s.active_cube == 0:
                nr1, nc1 = r + dr, c + dc
            else:
                nr2, nc2 = s.r2 + dr, s.c2 + dc

            # Kiểm tra nếu 2 khối đơn tiến lại đứng cạnh nhau -> Tự động ghép lại thành khối 1x1x2
            if nr1 == nr2 and abs(nc1 - nc2) == 1:
                return State(nr1, min(nc1, nc2), Orientation.LYING_H, mask)
            if nc1 == nc2 and abs(nr1 - nr2) == 1:
                return State(min(nr1, nr2), nc1, Orientation.LYING_V, mask)

            return State(nr1, nc1, Orientation.SPLIT, mask, nr2, nc2, s.active_cube)

        # TRƯỜNG HỢP 2: Khối nguyên 1x1x2 (Đứng, Nằm ngang, Nằm dọc)
        if ori == Orientation.STANDING:
            if action == "UP":    return State(r - 2, c, Orientation.LYING_V, mask)
            if action == "DOWN":  return State(r + 1, c, Orientation.LYING_V, mask)
            if action == "LEFT":  return State(r, c - 2, Orientation.LYING_H, mask)
            if action == "RIGHT": return State(r, c + 1, Orientation.LYING_H, mask)

        elif ori == Orientation.LYING_H:
            if action == "UP":    return State(r - 1, c, Orientation.LYING_H, mask)
            if action == "DOWN":  return State(r + 1, c, Orientation.LYING_H, mask)
            if action == "LEFT":  return State(r, c - 1, Orientation.STANDING, mask)
            if action == "RIGHT": return State(r, c + 2, Orientation.STANDING, mask)

        elif ori == Orientation.LYING_V:
            if action == "UP":    return State(r - 1, c, Orientation.STANDING, mask)
            if action == "DOWN":  return State(r + 2, c, Orientation.STANDING, mask)
            if action == "LEFT":  return State(r, c - 1, Orientation.LYING_V, mask)
            if action == "RIGHT": return State(r, c + 1, Orientation.LYING_V, mask)

        return None

    def _trigger_switches(self, prev_state: State, next_state: State, action: str) -> State:
        """Xử lý Soft switch, Heavy switch và Split switch khi khối vừa lăn tới ô mới."""
        if action == "SWITCH_CUBE":
            return next_state

        prev_cells = set(prev_state.get_occupied_cells())
        new_cells = [cell for cell in next_state.get_occupied_cells() if cell not in prev_cells]

        mask_list = list(next_state.bridges_mask)
        r, c, ori, r2, c2, active = (
            next_state.r, next_state.c, next_state.orientation,
            next_state.r2, next_state.c2, next_state.active_cube
        )

        for cell in new_cells:
            if cell not in self.switches:
                continue
            sw = self.switches[cell]
            sw_type = sw["type"]

            # 1. Soft switch: Bất kỳ phần nào của khối chạm vào đều kích hoạt
            if sw_type == "soft":
                self._update_bridges(mask_list, sw)

            # 2. Heavy switch: Chỉ kích hoạt khi khối 1x1x2 ĐỨNG THẲNG trên nó
            elif sw_type == "heavy" and ori == Orientation.STANDING:
                self._update_bridges(mask_list, sw)

            # 3. Split switch: Chỉ kích hoạt khi ĐỨNG THẲNG trên nó -> dịch chuyển & tách khối
            elif sw_type == "split" and ori == Orientation.STANDING:
                (tr1, tc1), (tr2, tc2) = sw["teleport_to"]
                ori = Orientation.SPLIT
                r, c, r2, c2, active = tr1, tc1, tr2, tc2, 0

        return State(r, c, ori, tuple(mask_list), r2, c2, active)

    def _update_bridges(self, mask_list: List[bool], sw: dict):
        for b_id in sw.get("target_bridges", []):
            idx = self.bridge_id_to_idx[b_id]
            if sw.get("behavior") == "toggle":
                mask_list[idx] = not mask_list[idx]
            else:  # permanent
                mask_list[idx] = bool(sw.get("fixed_state", True))