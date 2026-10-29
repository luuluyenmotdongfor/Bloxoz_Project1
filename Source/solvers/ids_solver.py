from typing import Dict, List, Optional, Set, Tuple

from core.state import State
from solvers.base_solver import BaseSolver


MAX_DEPTH = 100


class IDSSolver(BaseSolver):

    def _search(self) -> Optional[List[str]]:
        start_state = self.board.get_initial_state()
        if self.board.is_goal(start_state):
            return []

        for depth_limit in range(MAX_DEPTH + 1):
            path: List[str] = []
            path_states: Set[State] = {start_state}
            best_depth: Dict[State, int] = {}

            solution, cutoff = self._depth_limited_search(
                state=start_state,
                depth_limit=depth_limit,
                current_depth=0,
                path=path,
                path_states=path_states,
                best_depth=best_depth,
            )

            if solution is not None:
                return solution
            if self.status != "UNSOLVABLE":
                return None
            if not cutoff:
                return None

        # Không tìm thấy đáp án trong giới hạn độ sâu cho phép (depth limit).
        self.status = "DEPTH_LIMIT"
        return None

    def _depth_limited_search(
        self,
        state: State,
        depth_limit: int,
        current_depth: int,
        path: List[str],
        path_states: Set[State],
        best_depth: Dict[State, int],
    ) -> Tuple[Optional[List[str]], bool]:
        if self._limit_reached():
            return None, False
        
        if self.board.is_goal(state):
            return list(path), False

        previous_depth = best_depth.get(state)
        if previous_depth is not None and previous_depth <= current_depth:
            return None, False

                
        if current_depth == depth_limit:
            return None, True

        best_depth[state] = current_depth
        self.expanded_nodes += 1
        cutoff = False

        for action, next_state in self.board.get_successors(state):
            # Tránh lặp chu trình trên đường đi hiện tại; các trạng thái này
            # sẽ được xét lại ở các vòng lặp giới hạn độ sâu tiếp theo, nơi
            # mà một đường đi dài hơn có thể sẽ là cần thiết.
            if next_state in path_states:
                continue

            path.append(action)
            path_states.add(next_state)
            solution, child_cutoff = self._depth_limited_search(
                state=next_state,
                depth_limit=depth_limit,
                current_depth=current_depth + 1,
                path=path,
                path_states=path_states,
                best_depth=best_depth,
            )
            path_states.remove(next_state)
            path.pop()

            if solution is not None:
                return solution, False
            if self.status != "UNSOLVABLE":
                return None, False
            cutoff = cutoff or child_cutoff

        return None, cutoff