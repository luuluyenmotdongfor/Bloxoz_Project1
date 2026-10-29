import argparse
import os
import sys
import csv
import json
import math
import platform
import statistics
import subprocess
from datetime import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.board import Board
from solvers.bfs_solver import BFSSolver
from solvers.dfs_solver import DFSSolver
from solvers.ids_solver import IDSSolver, MAX_DEPTH
from solvers.ucs_solver import UCSSolver
from solvers.astar_solver import AStarSolver

SOLVERS = {
    "BFS": BFSSolver,
    "DFS": DFSSolver,
    "IDS": IDSSolver,
    "UCS": UCSSolver,
    "A*": AStarSolver,
}


def verify_solution(board: Board, actions: list):
    """Kiểm tra xem danh sách bước đi của thuật toán có thực sự dẫn tới đích hợp lệ không."""
    state = board.get_initial_state()
    total_cost = 0
    cost_solver = UCSSolver(board)
    if not board.is_valid_state(state):
        return False, None
    for act in actions:
        nxt = board._apply_move(state, act)
        if nxt is None or not board.is_valid_state(nxt):
            return False, None
        state = board._trigger_switches(state, nxt, act)
        if not board.is_valid_state(state):
            return False, None
        total_cost += cost_solver._get_step_cost(act, state)
    return board.is_goal(state), round(total_cost, 6)


def get_machine_info(machine_label):
    info = {
        "machine_label": machine_label,
        "os": platform.platform(),
        "python": platform.python_version(),
        "matplotlib": matplotlib.__version__,
        "cpu": platform.processor(),
        "ram_gib": None,
        "gpu": [],
        "execution": "CPU, one solver at a time",
    }
    if platform.system() == "Windows":
        command = (
            "$cs = Get-CimInstance Win32_ComputerSystem; "
            "[pscustomobject]@{"
            "cpu = (Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name); "
            "ram_gib = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2); "
            "gpu = @(Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name)"
            "} | ConvertTo-Json -Compress"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True, text=True, check=True, timeout=15,
            )
            info.update(json.loads(result.stdout))
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            info["hardware_read_error"] = str(error)
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=BASE_DIR,
            capture_output=True, text=True, check=True, timeout=5,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=BASE_DIR,
            capture_output=True, text=True, check=True, timeout=5,
        )
        info["git_commit"] = commit.stdout.strip()
        info["git_dirty"] = bool(status.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        info["git_commit"] = "unknown"
    return info


def summarize_results(rows, repeats):
    groups = {}
    for row in rows:
        key = (row["level"], row["algorithm"])
        groups.setdefault(key, []).append(row)

    summary = []
    for (level, algorithm), runs in groups.items():
        valid = [row for row in runs if row["status"] == "OK"]
        statuses = {row["status"] for row in runs}
        complete = len(runs) == repeats and len(valid) == repeats
        status = "OK" if complete else "PARTIAL"
        if not valid and len(statuses) == 1:
            status = runs[0]["status"]
        result = {
            "level": level, "algorithm": algorithm, "status": status,
            "successful_runs": len(valid), "repeats": repeats,
        }
        for key in ("solution_length", "solution_cost", "expanded_nodes",
                    "search_time_sec", "peak_memory_kib"):
            result[key] = statistics.median([row[key] for row in valid]) if complete else None
        summary.append(result)
    return summary


def run_benchmarks(repeats=3, time_limit=10.0, node_limit=250000, machine_label=""):
    levels_dir = os.path.join(BASE_DIR, "levels")

    level_files = sorted([f for f in os.listdir(levels_dir) if f.endswith(".json")])
    if not level_files:
        print("Không tìm thấy file map .json nào trong Source/levels/!")
        return

    metadata = get_machine_info(machine_label)
    metadata.update({
        "started_at": datetime.now().astimezone().isoformat(),
        "repeats": repeats, "time_limit_sec": time_limit, "node_limit": node_limit,
        "ids_max_depth": MAX_DEPTH, "warmup_runs": 0,
        "algorithm_order": list(SOLVERS.keys()),
        "summary": "Median; only cases with all repeats OK are plotted",
        "time_measurement": "solver.solve search, with tracemalloc enabled; excludes replay and plotting",
        "memory_measurement": "tracemalloc peak Python allocations in KiB, not total process RAM",
        "expanded_nodes": "One count per Board.get_successors call inside search, including IDS cutoffs",
        "cost": "1 + 2*has_fragile + 2*is_split + 0.1*closed_bridges, evaluated at next_state",
        "completed": False,
        "warnings": [],
    })
    run_name = datetime.now().strftime("run_%Y%m%d_%H%M%S_%f")
    results_dir = os.path.join(BASE_DIR, "results", run_name)
    os.makedirs(results_dir)
    info_path = os.path.join(results_dir, "machine_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Đang chạy thực nghiệm với các thuật toán: {list(SOLVERS.keys())}")
    print("-" * 85)
    print(f"Mỗi trường hợp chạy {repeats} lần, giới hạn {time_limit}s / {node_limit} nodes mỗi lần.")
    print(f"{'Level':<20} | {'Algo':<5} | {'Run':<3} | {'Status':<12} | {'Length':<6} | {'Time (s)':<10} | {'Mem (KiB)':<10}")
    print("-" * 85)

    all_rows = []
    raw_path = os.path.join(results_dir, "benchmark_raw.csv")
    fields = ["level", "algorithm", "run", "status", "solution_length", "solution_cost",
              "expanded_nodes", "search_time_sec", "peak_memory_kib", "error"]
    with open(raw_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for lvl_file in level_files:
            lvl_path = os.path.join(levels_dir, lvl_file)
            board = Board(lvl_path)
            lvl_label = lvl_file.replace(".json", "")
            for (r, c), switch in board.switches.items():
                if switch["type"] == "split" and board.grid[r][c] == 2:
                    warning = f"{lvl_label}: Split tại ({r}, {c}) nằm trên Fragile, không thể kích hoạt."
                    metadata["warnings"].append(warning)
                    print(f"CẢNH BÁO: {warning}")

            for run in range(1, repeats + 1):
                for algo_name, solver_cls in SOLVERS.items():
                    row = dict.fromkeys(fields)
                    row.update(level=lvl_label, algorithm=algo_name, run=run, status="ERROR", error="")
                    try:
                        solver = solver_cls(board, time_limit=time_limit, node_limit=node_limit)
                        res = solver.solve()
                        row.update(status=res["status"], expanded_nodes=res["expanded_nodes"],
                                   search_time_sec=res["search_time_sec"], peak_memory_kib=res["peak_memory_kb"])
                        if res["solved"]:
                            is_valid, cost = verify_solution(board, res["actions"])
                            row["status"] = "OK" if is_valid else "INVALID"
                            if is_valid:
                                row["solution_length"] = res["solution_length"]
                                row["solution_cost"] = cost
                    except Exception as error:
                        row["status"] = "ERROR"
                        row["error"] = f"{type(error).__name__}: {error}"

                    all_rows.append(row)
                    writer.writerow(row)
                    f.flush()
                    print(f"{lvl_label:<20} | {algo_name:<5} | {run:<3} | {row['status']:<12} | "
                          f"{str(row['solution_length']):<6} | {str(row['search_time_sec']):<10} | "
                          f"{str(row['peak_memory_kib']):<10}")
                    if row["error"]:
                        print(row["error"])

    summary = summarize_results(all_rows, repeats)
    for lvl_file in level_files:
        level = lvl_file.replace(".json", "")
        results = {row["algorithm"]: row for row in summary if row["level"] == level}
        for first, second, key in [("BFS", "IDS", "solution_length"), ("UCS", "A*", "solution_cost")]:
            a, b = results[first], results[second]
            if a["status"] == b["status"] == "OK" and not math.isclose(a[key], b[key], rel_tol=1e-9, abs_tol=1e-9):
                warning = f"{level}: {first} và {second} khác {key}; cần kiểm tra lại."
                metadata["warnings"].append(warning)
                a["status"] = b["status"] = "CHECK_FAILED"
                print(f"CẢNH BÁO: {warning}")

    # 1. Lưu bảng CSV để dễ copy vào Excel / LaTeX / Word Report
    csv_path = os.path.join(results_dir, "benchmark_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)
    print("-" * 85)
    print(f"✅ Đã lưu bảng số liệu tại: {csv_path}")

    # 2. Vẽ biểu đồ so sánh các thông số
    metadata["chart_scales"] = plot_metrics(summary, level_files, results_dir)
    metadata["finished_at"] = datetime.now().astimezone().isoformat()
    metadata["completed"] = True
    metadata["successful_runs"] = sum(row["status"] == "OK" for row in all_rows)
    metadata["total_runs"] = len(all_rows)
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def draw_metric(ax, rows, levels, key, title):
    algos = list(SOLVERS.keys())
    x = range(len(levels))
    width = 0.8 / len(algos)
    plotted_values = []
    for i, algo in enumerate(algos):
        vals = []
        for lvl in levels:
            match = [r[key] for r in rows if r["level"] == lvl and r["algorithm"] == algo and r["status"] == "OK"]
            vals.append(match[0] if match else float("nan"))
        plotted_values.extend(value for value in vals if math.isfinite(value))
        offsets = [pos + (i - len(algos) / 2 + 0.5) * width for pos in x]
        ax.bar(offsets, vals, width=width, label=algo)

    scale = "linear"
    positive = [value for value in plotted_values if value > 0]
    if positive and max(positive) / min(positive) >= 30:
        scale = "symlog" if 0 in plotted_values else "log"
        if scale == "symlog":
            ax.set_yscale(scale, linthresh=min(positive))
        else:
            ax.set_yscale(scale)
    ax.set_xticks(list(x))
    ax.set_xticklabels([level.replace("level_", "") for level in levels], rotation=45, ha="right")
    ax.set_xlabel("Level")
    ax.set_ylabel(title)
    ax.set_title(f"{title} ({scale})")
    ax.legend(fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    return scale


def plot_metrics(rows, level_files, results_dir):
    levels = [f.replace(".json", "") for f in level_files]
    metrics = [
        ("search_time_sec", "Search Time (Seconds)", "chart_search_time.png"),
        ("peak_memory_kib", "Peak Python Memory (KiB)", "chart_memory.png"),
        ("expanded_nodes", "Number of Expanded Nodes", "chart_expanded_nodes.png"),
        ("solution_length", "Solution Length (Moves)", "chart_solution_length.png"),
        ("solution_cost", "Solution Cost", "chart_solution_cost.png"),
    ]
    scales = {}
    for key, title, filename in metrics:
        fig, ax = plt.subplots(figsize=(15, 6))
        scales[key] = draw_metric(ax, rows, levels, key, title)
        fig.suptitle("Bloxorz - median of complete successful runs; missing bars = no comparable result", fontsize=10)
        fig.tight_layout()
        out_path = os.path.join(results_dir, filename)
        fig.savefig(out_path, dpi=180)
        plt.close(fig)

    fig, axes = plt.subplots(3, 2, figsize=(18, 15))
    for ax, (key, title, _) in zip(axes.flat, metrics):
        draw_metric(ax, rows, levels, key, title)
    axes.flat[-1].axis("off")
    fig.suptitle("Bloxorz - median of complete successful runs; missing bars = no comparable result")
    fig.tight_layout()
    fig.savefig(os.path.join(results_dir, "bfs.jpg"), dpi=180)
    plt.close(fig)
    print(f"📊 Đã xuất 5 biểu đồ và bfs.jpg tại: {results_dir}")
    return scales


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bloxorz benchmark")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--time-limit", type=float, default=10.0)
    parser.add_argument("--node-limit", type=int, default=250000)
    parser.add_argument("--machine-label", default="")
    args = parser.parse_args()
    if args.repeats < 1 or not math.isfinite(args.time_limit) or args.time_limit <= 0 or args.node_limit < 1:
        parser.error("repeats, time-limit và node-limit phải là số dương.")
    run_benchmarks(args.repeats, args.time_limit, args.node_limit, args.machine_label)
