import os
import sys
import csv
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.board import Board
from solvers.bfs_solver import BFSSolver

# Tự động nạp các thuật toán đã được các thành viên cài đặt
SOLVERS = {"BFS": BFSSolver}

try:
    from solvers.dfs_solver import DFSSolver
    SOLVERS["DFS"] = DFSSolver
except Exception:
    pass

try:
    from solvers.ids_solver import IDSSolver
    SOLVERS["IDS"] = IDSSolver
except Exception:
    pass

try:
    from solvers.ucs_solver import UCSSolver
    SOLVERS["UCS"] = UCSSolver
except Exception:
    pass

try:
    from solvers.astar_solver import AStarSolver
    SOLVERS["A*"] = AStarSolver
except Exception:
    pass


def verify_solution(board: Board, actions: list) -> bool:
    """Kiểm tra xem danh sách bước đi của thuật toán có thực sự dẫn tới đích hợp lệ không."""
    state = board.get_initial_state()
    for act in actions:
        nxt = board._apply_move(state, act)
        if nxt is None or not board.is_valid_state(nxt):
            return False
        state = board._trigger_switches(state, nxt, act)
        if not board.is_valid_state(state):
            return False
    return board.is_goal(state)


def run_benchmarks():
    levels_dir = os.path.join(BASE_DIR, "levels")
    results_dir = os.path.join(BASE_DIR, "results")
    os.makedirs(results_dir, exist_ok=True)

    level_files = sorted([f for f in os.listdir(levels_dir) if f.endswith(".json")])
    if not level_files:
        print("Không tìm thấy file map .json nào trong Source/levels/!")
        return

    print(f"Đang chạy thực nghiệm với các thuật toán: {list(SOLVERS.keys())}")
    print("-" * 85)
    print(f"{'Level':<15} | {'Algo':<6} | {'Solved':<8} | {'Length':<8} | {'Nodes':<10} | {'Time (s)':<10} | {'Mem (KB)':<10}")
    print("-" * 85)

    all_rows = []
    for lvl_file in level_files:
        lvl_path = os.path.join(levels_dir, lvl_file)
        board = Board(lvl_path)
        lvl_label = lvl_file.replace(".json", "")

        for algo_name, solver_cls in SOLVERS.items():
            solver = solver_cls(board)
            res = solver.solve()
            is_valid = verify_solution(board, res["actions"]) if res["solved"] else False
            status = "OK" if is_valid else ("INVALID" if res["solved"] else "FAIL")

            print(
                f"{lvl_label:<15} | {algo_name:<6} | {status:<8} | "
                f"{res['solution_length']:<8} | {res['expanded_nodes']:<10} | "
                f"{res['search_time_sec']:<10.6f} | {res['peak_memory_kb']:<10.2f}"
            )

            all_rows.append({
                "level": lvl_label,
                "algorithm": algo_name,
                "status": status,
                "solution_length": res["solution_length"],
                "expanded_nodes": res["expanded_nodes"],
                "search_time_sec": res["search_time_sec"],
                "peak_memory_kb": res["peak_memory_kb"]
            })

    # 1. Lưu bảng CSV để dễ copy vào Excel / LaTeX / Word Report
    csv_path = os.path.join(results_dir, "benchmark_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        writer.writeheader()
        writer.writerows(all_rows)
    print("-" * 85)
    print(f"✅ Đã lưu bảng số liệu tại: {csv_path}")

    # 2. Vẽ biểu đồ so sánh 4 thông số
    plot_metrics(all_rows, level_files, results_dir)


def plot_metrics(rows, level_files, results_dir):
    levels = [f.replace(".json", "") for f in level_files]
    algos = list(SOLVERS.keys())
    metrics = [
        ("search_time_sec", "Search Time (Seconds)", "chart_search_time.png"),
        ("peak_memory_kb", "Peak Memory Usage (KB)", "chart_memory.png"),
        ("expanded_nodes", "Number of Expanded Nodes", "chart_expanded_nodes.png"),
        ("solution_length", "Solution Length (Moves)", "chart_solution_length.png"),
    ]

    x = range(len(levels))
    width = 0.8 / max(len(algos), 1)

    for key, title, filename in metrics:
        plt.figure(figsize=(10, 5))
        for i, algo in enumerate(algos):
            vals = []
            for lvl in levels:
                match = [r[key] for r in rows if r["level"] == lvl and r["algorithm"] == algo]
                vals.append(match[0] if match else 0)
            offsets = [pos + (i - len(algos) / 2 + 0.5) * width for pos in x]
            plt.bar(offsets, vals, width=width, label=algo)

        plt.xticks(list(x), levels, rotation=25)
        plt.ylabel(title)
        plt.title(f"Bloxorz Solver Comparison - {title}")
        plt.legend()
        plt.grid(axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        out_path = os.path.join(results_dir, filename)
        plt.savefig(out_path, dpi=150)
        plt.close()

    print(f"📊 Đã xuất 4 biểu đồ so sánh (.png) tại thư mục: {results_dir}")


if __name__ == "__main__":
    run_benchmarks()
