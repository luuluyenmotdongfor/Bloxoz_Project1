import os
import sys
from flask import Flask, jsonify, request, send_from_directory

# Đảm bảo Python luôn tìm thấy thư mục core và solvers dù chạy lệnh từ đâu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.board import Board
from core.state import State, Orientation
from solvers.bfs_solver import BFSSolver
# Khi nhóm code xong 3 thuật toán còn lại thì mở comment 3 dòng dưới:
# from solvers.dfs_solver import DFSSolver
# from solvers.ucs_solver import UCSSolver
# from solvers.astar_solver import AStarSolver

app = Flask(__name__, static_folder=os.path.join(BASE_DIR, "gui"))
LEVELS_DIR = os.path.join(BASE_DIR, "levels")


def state_to_dict(state: State, board: Board):
    """Chuyển đối tượng State của Python sang JSON để GUI 3D vẽ lên màn hình."""
    return {
        "r": state.r,
        "c": state.c,
        "orientation": int(state.orientation),
        "bridges_mask": list(state.bridges_mask),
        "r2": state.r2,
        "c2": state.c2,
        "active_cube": state.active_cube,
        "occupied_cells": state.get_occupied_cells(),
        "is_goal": board.is_goal(state)
    }


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/levels", methods=["GET"])
def get_levels():
    files = sorted([f for f in os.listdir(LEVELS_DIR) if f.endswith(".json")])
    return jsonify({"levels": files})


@app.route("/api/level/<filename>", methods=["GET"])
def load_level(filename):
    path = os.path.join(LEVELS_DIR, filename)
    board = Board(path)
    init_state = board.get_initial_state()
    return jsonify({
        "name": board.name,
        "rows": board.rows,
        "cols": board.cols,
        "grid": board.grid,
        "start": board.start_pos,
        "goal": board.goal_pos,
        "bridge_cells": {
            f"{r},{c}": idx for (r, c), idx in board.cell_to_bridge_idx.items()
        },
        "switches": [
            {"pos": list(pos), "type": sw["type"]}
            for pos, sw in board.switches.items()
        ],
        "initial_state": state_to_dict(init_state, board)
    })


@app.route("/api/move", methods=["POST"])
def manual_move():
    """API xử lý khi người chơi bấm phím mũi tên / Space trên bàn phím."""
    data = request.json
    board = Board(os.path.join(LEVELS_DIR, data["level"]))
    s = data["state"]
    current_state = State(
        r=s["r"],
        c=s["c"],
        orientation=Orientation(s["orientation"]),
        bridges_mask=tuple(s["bridges_mask"]),
        r2=s.get("r2"),
        c2=s.get("c2"),
        active_cube=s.get("active_cube", 0)
    )
    action = data["action"]

    next_state = board._apply_move(current_state, action)
    if next_state is None or not board.is_valid_state(next_state):
        return jsonify({"valid": False, "reason": "Khối bị rơi khỏi bàn cờ hoặc làm vỡ gạch cam!"})

    final_state = board._trigger_switches(current_state, next_state, action)
    if not board.is_valid_state(final_state):
        return jsonify({"valid": False, "reason": "Cầu đóng làm khối rơi xuống vực!"})

    return jsonify({
        "valid": True,
        "state": state_to_dict(final_state, board)
    })


@app.route("/api/solve", methods=["POST"])
def solve_level():
    """API chạy thuật toán tìm kiếm và trả về lộ trình lăn khối từ đầu tới đích."""
    data = request.json
    level_file = data["level"]
    algo = data.get("algo", "bfs").lower()

    board = Board(os.path.join(LEVELS_DIR, level_file))

    solver_map = {
        "bfs": BFSSolver,
        # Mở comment khi các bạn trong nhóm code xong:
        # "dfs": DFSSolver,
        # "ucs": UCSSolver,
        # "astar": AStarSolver,
    }

    if algo not in solver_map:
        return jsonify({"error": f"Thuật toán '{algo.upper()}' đang được thành viên nhóm cài đặt!"}), 400

    solver = solver_map[algo](board)
    result = solver.solve()

    # Dựng lại danh sách các trạng thái liên tiếp để GUI 3D tự động lăn khối tới đích
    trace = []
    if result["solved"]:
        curr = board.get_initial_state()
        trace.append(state_to_dict(curr, board))
        for act in result["actions"]:
            nxt = board._apply_move(curr, act)
            curr = board._trigger_switches(curr, nxt, act)
            trace.append(state_to_dict(curr, board))

    result["trace"] = trace
    return jsonify(result)


if __name__ == "__main__":
    print("🚀 Khởi chạy Bloxorz 3D tại địa chỉ: http://127.0.0.1:5000")
    app.run(debug=True, port=5000)