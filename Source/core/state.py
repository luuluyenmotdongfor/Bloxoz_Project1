from enum import IntEnum
from typing import Tuple, Optional

class Orientation(IntEnum):
    STANDING = 0          # Đứng thẳng tại 1 ô (r, c)
    LYING_H = 1           # Nằm ngang chiếm (r, c) và (r, c + 1)
    LYING_V = 2           # Nằm dọc chiếm (r, c) và (r + 1, c)
    SPLIT = 3             # Tách thành 2 khối 1x1x1 tại (r, c) và (r2, c2)

class State:
    """
    Biểu diễn một trạng thái đầy đủ của bài toán tìm kiếm Bloxorz.
    Bắt buộc phải bất biến (immutable) và băm được (hashable) để đưa vào tập visited.
    """
    def __init__(
        self,
        r: int,
        c: int,
        orientation: Orientation,
        bridges_mask: Tuple[bool, ...],
        r2: Optional[int] = None,
        c2: Optional[int] = None,
        active_cube: int = 0  # 0 hoặc 1 (chỉ dùng khi đang ở trạng thái SPLIT)
    ):
        self.r = r
        self.c = c
        self.orientation = orientation
        self.bridges_mask = bridges_mask  # Tuple lưu trạng thái Đóng/Mở của mọi cây cầu
        self.r2 = r2
        self.c2 = c2
        self.active_cube = active_cube

    def get_occupied_cells(self):
        """Trả về danh sách các tọa độ (row, col) mà khối đang đè lên."""
        if self.orientation == Orientation.STANDING:
            return [(self.r, self.c)]
        elif self.orientation == Orientation.LYING_H:
            return [(self.r, self.c), (self.r, self.c + 1)]
        elif self.orientation == Orientation.LYING_V:
            return [(self.r, self.c), (self.r + 1, self.c)]
        elif self.orientation == Orientation.SPLIT:
            return [(self.r, self.c), (self.r2, self.c2)]
        return []

    def _key(self):
        """Khóa định danh trạng thái dùng cho tập visited (tránh lặp trạng thái)."""
        if self.orientation == Orientation.SPLIT:
            return (self.r, self.c, self.r2, self.c2, self.active_cube, self.orientation, self.bridges_mask)
        return (self.r, self.c, self.orientation, self.bridges_mask)

    def __hash__(self):
        return hash(self._key())

    def __eq__(self, other):
        return isinstance(other, State) and self._key() == other._key()

    def __lt__(self, other):
        # Hỗ trợ so sánh trong PriorityQueue (heapq) của UCS và A* khi có cùng độ ưu tiên
        if self.orientation == Orientation.SPLIT and other.orientation != Orientation.SPLIT:
            return True
        if self.orientation != Orientation.SPLIT and other.orientation == Orientation.SPLIT:
            return False
        return self._key() < other._key()