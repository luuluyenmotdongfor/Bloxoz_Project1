from core.state import Orientation
from solvers.search_utils import step_cost_units


def configuration_errors(board):
    errors = []
    if any(len(row) != board.cols for row in board.grid):
        return ["Grid must be rectangular"]

    def inside(cell):
        return len(cell) == 2 and 0 <= cell[0] < board.rows and 0 <= cell[1] < board.cols

    def supported(cell):
        return inside(cell) and (board.grid[cell[0]][cell[1]] != 0
                                or tuple(cell) in board.cell_to_bridge_idx)

    if not inside(board.start_pos) or not board.is_valid_state(board.get_initial_state()):
        errors.append("Invalid start")
    if not supported(board.goal_pos) or board.grid[board.goal_pos[0]][board.goal_pos[1]] == 2:
        errors.append("Invalid goal")
    for cell in board.cell_to_bridge_idx:
        if not inside(cell):
            errors.append(f"Bridge outside grid: {cell}")
    for cell, switch in board.switches.items():
        kind = switch.get("type")
        if kind not in {"soft", "heavy", "split"}:
            errors.append(f"Unknown switch type at {cell}")
        if not supported(cell):
            errors.append(f"Unsupported switch at {cell}")
            continue
        if kind in {"heavy", "split"} and board.grid[cell[0]][cell[1]] == 2:
            errors.append(f"{kind} switch on fragile tile at {cell}")
        if kind == "split":
            targets = switch.get("teleport_to", [])
            if len(targets) != 2 or any(not supported(target) for target in targets):
                errors.append(f"Invalid teleport targets at {cell}")
            elif tuple(targets[0]) == tuple(targets[1]):
                errors.append(f"Overlapping teleport targets at {cell}")
        else:
            for bridge in switch.get("target_bridges", []):
                if bridge not in board.bridge_id_to_idx:
                    errors.append(f"Unknown bridge {bridge} at {cell}")
    return errors


def replay_solution(board, actions):
    state = board.get_initial_state()
    if not board.is_valid_state(state):
        raise ValueError("Invalid initial state")
    cost = switches = splits = 0
    activated = []
    for action in actions:
        next_state = dict(board.get_successors(state)).get(action)
        if next_state is None:
            raise ValueError(f"Invalid action {action}")
        cost += step_cost_units(board, next_state)
        switches += action == "SWITCH_CUBE"
        if state.orientation != Orientation.SPLIT and next_state.orientation == Orientation.SPLIT:
            intermediate = board._apply_move(state, action)
            activated.append(f"{intermediate.r},{intermediate.c}")
            splits += 1
        state = next_state
    if not board.is_goal(state):
        raise ValueError("Final state is not the goal")
    return {
        "path_cost": cost / 10,
        "solution_length": len(actions),
        "switch_cube_count": switches,
        "split_count": splits,
        "activated_split_switches": "|".join(sorted(set(activated))),
    }
