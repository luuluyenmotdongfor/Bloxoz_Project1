import argparse
import os
import sys
import csv
import json
import math
import platform
import statistics
import subprocess
import hashlib
import tempfile
import time
import tracemalloc
from collections import deque
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
from solvers.search_utils import Heuristic, get_step_cost

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
    split_switches = set()
    switch_cube_count = 0
    if not board.is_valid_state(state):
        raise ValueError("Invalid initial state")
    for act in actions:
        next_state = dict(board.get_successors(state)).get(act)
        if next_state is None:
            raise ValueError(f"Invalid action: {act}")
        if state.orientation != 3 and next_state.orientation == 3:
            landing = board._apply_move(state, act)
            split_switches.add((landing.r, landing.c))
        switch_cube_count += act == "SWITCH_CUBE"
        total_cost += get_step_cost(board, next_state)
        state = next_state
    if not board.is_goal(state):
        raise ValueError("The returned path does not reach the goal")
    return {
        "solution_cost_units": total_cost,
        "solution_cost": total_cost / 10,
        "activated_split_switches": sorted(split_switches),
        "switch_cube_count": switch_cube_count,
    }


def source_hashes():
    hashes = {}
    for folder in ("core", "solvers", "levels", "gui"):
        for name in sorted(os.listdir(os.path.join(BASE_DIR, folder))):
            if name.endswith((".py", ".json", ".html")):
                relative = folder + "/" + name
                with open(os.path.join(BASE_DIR, relative), "rb") as f:
                    hashes[relative] = hashlib.sha256(f.read()).hexdigest()
    for name in ("main.py", "benchmark_report.py", "validate_levels.py"):
        with open(os.path.join(BASE_DIR, name), "rb") as f:
            hashes[name] = hashlib.sha256(f.read()).hexdigest()
    return hashes


def measure_solver(board, solver_cls, time_limit, node_limit):
    # Start tracing before construction; solve() reuses the existing trace.
    tracemalloc.start()
    started = time.perf_counter()
    try:
        solver = solver_cls(board, time_limit=time_limit, node_limit=node_limit)
        setup_time = time.perf_counter() - started
        _, setup_peak = tracemalloc.get_traced_memory()
        result = solver.solve()
        result["total_time_sec"] = time.perf_counter() - started
        result["setup_time_sec"] = setup_time
        result["peak_memory_kib"] = max(result["peak_memory_kb"], setup_peak / 1024)
        return result
    finally:
        tracemalloc.stop()


def quick_checks():
    cases = [
        ("already_at_goal", [[9]], [0, 0], [0, 0], True, 0),
        ("unsolvable", [[1, 0, 0, 9]], [0, 0], [0, 3], False, None),
        ("two_moves", [[1, 1, 1, 9]], [0, 0], [0, 3], True, 2),
    ]
    checks = []
    with tempfile.TemporaryDirectory() as folder:
        for case, grid, start, goal, solved, length in cases:
            filename = os.path.join(folder, case + ".json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump({"grid": grid, "start": start, "goal": goal}, f)
            for algorithm, solver_cls in SOLVERS.items():
                entry = {"case": case, "algorithm": algorithm, "status": "PASS"}
                try:
                    board = Board(filename)
                    original = board.get_successors
                    calls = 0

                    def counted(state):
                        nonlocal calls
                        calls += 1
                        return original(state)

                    board.get_successors = counted
                    result = solver_cls(board, time_limit=2, node_limit=10000).solve()
                    board.get_successors = original
                    if result["solved"] != solved:
                        raise ValueError(f"Expected solved={solved}, got {result['solved']}")
                    if result["expanded_nodes"] != calls:
                        raise ValueError(f"Expanded count {result['expanded_nodes']} differs from {calls} successor calls")
                    if solved:
                        verify_solution(board, result["actions"])
                        if result["solution_length"] != length:
                            raise ValueError(f"Expected {length} moves, got {result['solution_length']}")
                    elif result["status"] != "UNSOLVABLE":
                        raise ValueError(f"Unexpected status: {result['status']}")
                except Exception as error:
                    entry.update(status="FAIL", error=f"{type(error).__name__}: {error}")
                checks.append(entry)
                print(f"CHECK {case:18} {algorithm:4} {entry['status']} {entry.get('error', '')}")
    return checks


def inspect_map(board):
    errors = []
    if any(len(row) != board.cols for row in board.grid):
        return ["Rows have different lengths"]

    def supported(pos):
        r, c = pos
        return (0 <= r < board.rows and 0 <= c < board.cols
                and (board.grid[r][c] != 0 or tuple(pos) in board.cell_to_bridge_idx))

    if not board.is_valid_state(board.get_initial_state()):
        errors.append("Invalid initial state")
    if not supported(board.goal_pos) or board.grid[board.goal_pos[0]][board.goal_pos[1]] == 2:
        errors.append("Invalid goal tile")
    for pos, switch in board.switches.items():
        if not supported(pos):
            errors.append(f"Unsupported switch at {pos}")
        elif switch["type"] in ("heavy", "split") and board.grid[pos[0]][pos[1]] == 2:
            errors.append(f"{switch['type']} on fragile at {pos}")
        for bridge_id in switch.get("target_bridges", []):
            if bridge_id not in board.bridge_ids:
                errors.append(f"Unknown bridge: {bridge_id}")
        if switch["type"] == "split":
            targets = switch.get("teleport_to", [])
            if len(targets) != 2 or len({tuple(p) for p in targets}) != 2:
                errors.append(f"Invalid split targets at {pos}")
            elif any(not supported(p) for p in targets):
                errors.append(f"Unsupported split target at {pos}")
    return errors


def check_heuristic(board, time_limit=2.0, state_limit=10000):
    started = time.perf_counter()
    heuristic = Heuristic(board)
    initial = board.get_initial_state()
    frontier = deque([initial])
    visited = {initial}
    activated = set()
    errors = []
    checked = 0
    edge_count = 0
    while frontier and checked < state_limit and time.perf_counter() - started < time_limit:
        state = frontier.popleft()
        checked += 1
        h = heuristic(state)
        if not math.isfinite(h) or h < 0:
            errors.append(f"Invalid h={h} at {state._key()}")
            break
        if board.is_goal(state):
            if h != 0:
                errors.append(f"Goal heuristic is {h}, expected 0")
            continue
        for action, next_state in board.get_successors(state):
            edge_count += 1
            cost = get_step_cost(board, next_state)
            next_h = heuristic(next_state)
            if h > cost + next_h + 1e-9:
                errors.append(f"Inconsistent edge: {state._key()} --{action}--> {next_state._key()}; {h} > {cost} + {next_h}")
                break
            if state.orientation != 3 and next_state.orientation == 3:
                landing = board._apply_move(state, action)
                activated.add((landing.r, landing.c))
            if next_state not in visited:
                visited.add(next_state)
                frontier.append(next_state)
        if errors:
            break
    expected = {pos for pos, switch in board.switches.items() if switch["type"] == "split"}
    complete = not frontier and not errors
    return {
        "status": "FAIL" if errors else ("COMPLETE" if complete else "LIMIT"),
        "checked_states": checked, "checked_edges": edge_count,
        "errors": errors, "activated_split_switches": sorted(activated),
        "unseen_split_switches": sorted(expected - activated),
        "coverage_note": "Unseen is not proof of unreachable when status=LIMIT",
    }


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
            ["git", "status", "--porcelain", "--", "*.py", "core/*.py", "solvers/*.py", "levels/*.json", "gui/index.html"], cwd=BASE_DIR,
            capture_output=True, text=True, check=True, timeout=5,
        )
        info["git_commit"] = commit.stdout.strip()
        info["git_source_dirty"] = bool(status.stdout.strip())
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
        for key in ("solution_length", "solution_cost_units", "solution_cost", "expanded_nodes",
                    "setup_time_sec", "search_time_sec", "total_time_sec", "peak_memory_kib"):
            result[key] = statistics.median([row[key] for row in valid]) if complete else None
        for key in ("total_time_sec", "peak_memory_kib"):
            result[key + "_min"] = min(row[key] for row in valid) if complete else None
            result[key + "_max"] = max(row[key] for row in valid) if complete else None
        summary.append(result)
    return summary


def run_benchmarks(repeats=3, time_limit=10.0, node_limit=250000, machine_label="", check_only=False):
    levels_dir = os.path.join(BASE_DIR, "levels")

    level_files = sorted([f for f in os.listdir(levels_dir) if f.endswith(".json")])
    if not level_files:
        print("Không tìm thấy file map .json nào trong Source/levels/!")
        return 1

    metadata = get_machine_info(machine_label)
    metadata.update({
        "started_at": datetime.now().astimezone().isoformat(),
        "repeats": repeats, "time_limit_sec": time_limit, "node_limit": node_limit,
        "ids_max_depth": MAX_DEPTH, "warmup_runs": 0,
        "preflight_small_fixtures": True,
        "quick_check_time_limit_sec": 2,
        "quick_check_node_limit": 10000,
        "heuristic_check_time_limit_sec": 2.0,
        "heuristic_check_state_limit": 10000,
        "expected_runs": 0 if check_only else len(level_files) * len(SOLVERS) * repeats,
        "algorithm_order": list(SOLVERS.keys()),
        "summary": "Median; only cases with all repeats OK and cross-checks consistent are plotted",
        "time_measurement": "total_time_sec includes solver construction and solve, with tracemalloc enabled; excludes Board loading, replay, checks and plotting",
        "time_limit_scope": "BaseSolver.solve; constructor time is additionally measured and reported",
        "memory_measurement": "tracemalloc peak new Python allocations from solver construction through solve, in KiB; not process RAM or GPU memory",
        "expanded_nodes": "One count per Board.get_successors call inside search; heuristic cell preprocessing is not a search-state expansion",
        "cost_units": "10 + 20*has_fragile + 20*is_split + closed_bridges, evaluated at next_state",
        "reported_cost": "solution_cost_units / 10",
        "heuristic": "Active Heuristic.__call__; prototype get_heuristic is not called",
        "source_hashes": source_hashes(),
        "mode": "check_only" if check_only else "benchmark",
        "completed": False,
        "warnings": [],
    })
    run_name = datetime.now().strftime("report_%Y%m%d_%H%M%S_%f")
    results_dir = os.path.join(BASE_DIR, "results", run_name)
    os.makedirs(results_dir)
    info_path = os.path.join(results_dir, "machine_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"Thư mục kết quả: {results_dir}")
    checks = {"quick_checks": quick_checks(), "maps": [], "comparisons": []}
    checks_path = os.path.join(results_dir, "checks.json")
    quick_ok = all(check["status"] == "PASS" for check in checks["quick_checks"])
    if check_only:
        for lvl_file in level_files:
            entry = {"level": lvl_file.replace(".json", "")}
            try:
                board = Board(os.path.join(levels_dir, lvl_file))
                errors = inspect_map(board)
                if errors:
                    entry.update(status="FAIL", errors=errors)
                else:
                    entry.update(check_heuristic(board))
            except Exception as error:
                entry.update(status="FAIL", errors=[f"{type(error).__name__}: {error}"])
            checks["maps"].append(entry)
            print(f"MAP {entry['level']:20} {entry['status']:8} states={entry.get('checked_states', 0)} "
                  f"unseen_split={entry.get('unseen_split_switches', [])} {entry.get('errors', [])}")
    with open(checks_path, "w", encoding="utf-8") as f:
        json.dump(checks, f, ensure_ascii=False, indent=2)
    if check_only or not quick_ok:
        metadata["completed"] = True
        metadata["finished_at"] = datetime.now().astimezone().isoformat()
        metadata["sources_changed"] = metadata["source_hashes"] != source_hashes()
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        ok = quick_ok and all(entry["status"] != "FAIL" for entry in checks["maps"])
        print("LIMIT nghĩa là chưa duyệt hết đồ thị; không đồng nghĩa với lỗi hoặc vô nghiệm.")
        print("Kiểm tra xong." if ok else "Có lỗi: xem checks.json trước khi chạy benchmark.")
        return 0 if ok and not metadata["sources_changed"] else 1

    print(f"Đang chạy thực nghiệm với các thuật toán: {list(SOLVERS.keys())}")
    print("-" * 85)
    print(f"Mỗi trường hợp chạy {repeats} lần, giới hạn {time_limit}s / {node_limit} nodes mỗi lần.")
    print(f"{'Level':<20} | {'Algo':<5} | {'Run':<3} | {'Status':<12} | {'Length':<6} | {'Time (s)':<10} | {'Mem (KiB)':<10}")
    print("-" * 85)

    all_rows = []
    raw_path = os.path.join(results_dir, "benchmark_raw.csv")
    fields = ["level", "algorithm", "run", "status", "solution_length", "solution_cost_units", "solution_cost",
              "expanded_nodes", "setup_time_sec", "search_time_sec", "total_time_sec", "peak_memory_kib", "error"]
    solutions_path = os.path.join(results_dir, "solutions.jsonl")
    with open(raw_path, "w", newline="", encoding="utf-8-sig") as f, open(solutions_path, "w", encoding="utf-8") as paths_file:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for lvl_file in level_files:
            lvl_path = os.path.join(levels_dir, lvl_file)
            lvl_label = lvl_file.replace(".json", "")
            try:
                board = Board(lvl_path)
                map_errors = inspect_map(board)
            except Exception as error:
                map_errors = [f"{type(error).__name__}: {error}"]
            if map_errors:
                metadata["warnings"].append({"level": lvl_label, "errors": map_errors})

            for run in range(1, repeats + 1):
                for algo_name, solver_cls in SOLVERS.items():
                    row = dict.fromkeys(fields)
                    row.update(level=lvl_label, algorithm=algo_name, run=run, status="ERROR", error="")
                    try:
                        if map_errors:
                            raise ValueError("; ".join(map_errors))
                        res = measure_solver(board, solver_cls, time_limit, node_limit)
                        row["status"] = res["status"]
                        for key in ("expanded_nodes", "setup_time_sec", "search_time_sec", "total_time_sec", "peak_memory_kib"):
                            row[key] = res[key]
                        if res["solved"]:
                            try:
                                details = verify_solution(board, res["actions"])
                                if res["solution_length"] != len(res["actions"]):
                                    raise ValueError("solution_length differs from actions length")
                                row["status"] = "OK"
                                row["solution_length"] = res["solution_length"]
                                row["solution_cost_units"] = details["solution_cost_units"]
                                row["solution_cost"] = details["solution_cost"]
                                record = {"level": lvl_label, "algorithm": algo_name, "run": run,
                                          "actions": res["actions"], **details}
                                paths_file.write(json.dumps(record, ensure_ascii=False) + "\n")
                                paths_file.flush()
                            except ValueError as error:
                                row.update(status="INVALID", error=str(error))
                    except Exception as error:
                        row["status"] = "ERROR"
                        row["error"] = f"{type(error).__name__}: {error}"

                    all_rows.append(row)
                    writer.writerow(row)
                    f.flush()
                    print(f"{lvl_label:<20} | {algo_name:<5} | {run:<3} | {row['status']:<12} | "
                          f"{str(row['solution_length']):<6} | {str(round(row['total_time_sec'], 6) if row['total_time_sec'] is not None else '-'):10} | "
                          f"{str(round(row['peak_memory_kib'], 2) if row['peak_memory_kib'] is not None else '-'):10}")
                    if row["error"]:
                        print(row["error"])

    summary = summarize_results(all_rows, repeats)
    for lvl_file in level_files:
        level = lvl_file.replace(".json", "")
        for run in range(1, repeats + 1):
            results = {row["algorithm"]: row for row in all_rows if row["level"] == level and row["run"] == run}
            for first, second, key in [("BFS", "IDS", "solution_length"), ("UCS", "A*", "solution_cost_units")]:
                a, b = results[first], results[second]
                result = {"level": level, "run": run, "pair": [first, second], "metric": key, "status": "SKIPPED"}
                if a["status"] == b["status"] == "OK":
                    result.update(status="PASS" if a[key] == b[key] else "FAIL", values=[a[key], b[key]])
                checks["comparisons"].append(result)
                if result["status"] == "FAIL":
                    for row in summary:
                        if row["level"] == level and row["algorithm"] in (first, second):
                            row["status"] = "CHECK_FAILED"
            if any(row["status"] == "OK" for row in results.values()):
                for row in results.values():
                    if row["status"] == "UNSOLVABLE":
                        checks["comparisons"].append({"level": level, "run": run, "algorithm": row["algorithm"],
                                                      "status": "FAIL", "error": "Reports UNSOLVABLE while another solver found a valid path"})

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
    export_latex(summary, metadata, results_dir)
    metadata["finished_at"] = datetime.now().astimezone().isoformat()
    metadata["completed"] = True
    metadata["successful_runs"] = sum(row["status"] == "OK" for row in all_rows)
    metadata["total_runs"] = len(all_rows)
    metadata["sources_changed"] = metadata["source_hashes"] != source_hashes()
    metadata["comparison_failures"] = sum(check["status"] == "FAIL" for check in checks["comparisons"])
    metadata["error_runs"] = sum(row["status"] in ("ERROR", "INVALID") for row in all_rows)
    with open(checks_path, "w", encoding="utf-8") as f:
        json.dump(checks, f, ensure_ascii=False, indent=2)
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"Lượt OK: {metadata['successful_runs']}/{len(all_rows)}; đối chiếu sai: {metadata['comparison_failures']}.")
    if metadata["sources_changed"]:
        print("CẢNH BÁO: source đã thay đổi trong lúc chạy; cần chạy lại trên một phiên bản cố định.")
    print(f"Gửi lại thư mục này để cập nhật report: {results_dir}")
    return 1 if metadata["sources_changed"] or metadata["comparison_failures"] or metadata["error_runs"] else 0


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


def tex_escape(value):
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in str(value))


def export_latex(rows, metadata, results_dir):
    codes = {"OK": "OK", "TIME_LIMIT": "T", "NODE_LIMIT": "N", "DEPTH_LIMIT": "D",
             "UNSOLVABLE": "U", "ERROR": "E", "INVALID": "I", "PARTIAL": "P", "CHECK_FAILED": "C"}
    legend = ("OK: thành công; T: hết thời gian; N: hết giới hạn node; D: hết giới hạn sâu; "
              "U: báo vô nghiệm; E: lỗi thực thi; I: đường đi không hợp lệ; P: chỉ thành công một phần; C: đối chiếu không khớp.")
    lines = [legend, ""]
    for offset in range(0, len(rows), 10):
        lines += [r"\begin{table}[htbp]", r"\centering", r"\small",
                  r"\begin{tabular}{llrrrrrl}", r"\hline",
                  r"Level & Thuật toán & $L$ & $C$ & Nodes & ms & KiB & TT \\", r"\hline"]
        for row in rows[offset:offset + 10]:
            values = [row["level"].split("_")[1], row["algorithm"]]
            for key in ("solution_length", "solution_cost", "expanded_nodes", "total_time_sec", "peak_memory_kib"):
                value = row[key] if row["status"] == "OK" else None
                if value is None:
                    values.append("--")
                elif key in ("solution_length", "expanded_nodes"):
                    values.append(str(int(value)))
                else:
                    values.append(f"{value * 1000 if key == 'total_time_sec' else value:.3f}")
            values.append(codes.get(row["status"], row["status"]))
            lines.append(" & ".join(tex_escape(value) for value in values) + r" \\")
        lines += [r"\hline", r"\end{tabular}",
                  r"\caption{Kết quả thực nghiệm (trung vị của " + str(metadata["repeats"]) +
                  r" lần chạy). Thời gian gồm khởi tạo solver và tìm kiếm; $C$ bằng chi phí nguyên chia 10.}",
                  r"\end{table}", ""]
    with open(os.path.join(results_dir, "appendix_results.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    gpu = metadata.get("gpu", [])
    machine = [
        ("Máy", metadata.get("machine_label") or "Chưa nhập nhãn máy"),
        ("CPU", metadata.get("cpu") or "Chưa đọc được"),
        ("RAM (GiB)", metadata.get("ram_gib") if metadata.get("ram_gib") is not None else "Chưa đọc được"),
        ("GPU", ", ".join(gpu) if isinstance(gpu, list) else gpu),
        ("Hệ điều hành", metadata["os"]), ("Python", metadata["python"]),
        ("Matplotlib", metadata["matplotlib"]), ("Commit", metadata.get("git_commit", "unknown")),
        ("Số lần chạy", metadata["repeats"]),
        ("Giới hạn mỗi solve", f"{metadata['time_limit_sec']} s; {metadata['node_limit']} node; IDS sâu tối đa {metadata['ids_max_depth']}"),
        ("Phạm vi đo", "Khởi tạo solver và tìm kiếm trên CPU; bật tracemalloc; không gồm đọc map, kiểm tra lời giải và vẽ biểu đồ."),
    ]
    lines = [r"\begin{tabular}{p{0.24\linewidth}p{0.66\linewidth}}", r"\hline"]
    for label, value in machine:
        lines.append(tex_escape(label) + " & " + tex_escape(value) + r" \\")
    lines += [r"\hline", r"\end{tabular}"]
    with open(os.path.join(results_dir, "machine_info.tex"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def plot_metrics(rows, level_files, results_dir):
    levels = [f.replace(".json", "") for f in level_files]
    metrics = [
        ("total_time_sec", "Solver Setup + Search Time (Seconds)", "chart_search_time.png"),
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
    parser.add_argument("--check-only", action="store_true", help="Small correctness cases and bounded heuristic/Split checks; no performance benchmark")
    args = parser.parse_args()
    if args.repeats < 1 or not math.isfinite(args.time_limit) or args.time_limit <= 0 or args.node_limit < 1:
        parser.error("repeats, time-limit và node-limit phải là số dương.")
    sys.exit(run_benchmarks(args.repeats, args.time_limit, args.node_limit, args.machine_label, args.check_only))
