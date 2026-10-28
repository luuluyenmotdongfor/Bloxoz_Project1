import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from importlib.metadata import version
from pathlib import Path

from core.board import Board
from solvers.bfs_solver import BFSSolver
from solvers.dfs_solver import DFSSolver
from solvers.ids_solver import IDSSolver
from solvers.ucs_solver import UCSSolver
from solvers.astar_solver import AStarSolver
from validation import configuration_errors, replay_solution
from reporting import export_report

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parent
SOLVERS = {"BFS": BFSSolver, "DFS": DFSSolver, "IDS": IDSSolver,
           "UCS": UCSSolver, "A*": AStarSolver}
FIELDS = ["level", "algorithm", "repeat", "status", "solution_length", "path_cost",
          "expanded_nodes", "time_ms", "memory_kib", "switch_cube_count", "split_count",
          "activated_split_switches", "error"]


def command(args):
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=15, check=True)
    return result.stdout.strip()


def hardware_info():
    info = {"cpu": platform.processor() or "Không xác định"}
    if os.name == "nt":
        script = """
        [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
        $computer = Get-CimInstance Win32_ComputerSystem
        $cpu = (Get-CimInstance Win32_Processor | ForEach-Object { $_.Name }) -join '; '
        $gpu = (Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }) -join '; '
        [ordered]@{cpu=$cpu; gpu=$gpu; model=$computer.Model;
            ram=('{0:N2} GiB' -f ($computer.TotalPhysicalMemory / 1GB))} | ConvertTo-Json
        """
        try:
            info.update(json.loads(command(["powershell.exe", "-NoProfile", "-Command", script])))
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            info["detection_error"] = str(exc)
    else:
        try:
            info["ram"] = f"{os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE') / 2**30:.2f} GiB"
            cpuinfo = Path("/proc/cpuinfo")
            if cpuinfo.exists():
                names = [line.split(":", 1)[1].strip() for line in cpuinfo.read_text().splitlines()
                         if line.startswith("model name")]
                if names:
                    info["cpu"] = names[0]
        except (OSError, ValueError):
            pass
    return info


def metadata_for(args, paths):
    files = list(SOURCE.rglob("*.py")) + paths + [ROOT / "requirements.txt"]
    try:
        commit = command(["git", "rev-parse", "HEAD"])
        dirty = bool(command(["git", "status", "--porcelain"]))
    except (OSError, subprocess.SubprocessError):
        commit, dirty = "UNKNOWN", True
    return {
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "machine_label": args.machine_label,
        "hardware": hardware_info(),
        "os": platform.platform(),
        "python": sys.version.splitlines()[0],
        "matplotlib": version("matplotlib"),
        "commit": commit,
        "dirty": dirty,
        "repeats": args.repeats,
        "time_limit": args.time_limit,
        "node_limit": args.node_limit,
        "max_depth_ids": args.max_depth,
        "warmups": 0,
        "tracemalloc": True,
        "time_scope": "_search including heuristic preprocessing; excludes replay and reporting",
        "node_definition": "one count per call to Board.get_successors during search, including IDS cutoffs",
        "cost": "1 + 2*has_fragile(next) + 2*is_split(next) + 0.1*closed_bridges(next)",
        "levels": [path.stem for path in paths],
        "sha256": {str(path.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in files},
        "completed": False,
    }


def run_case(path, algorithm, repeat, args):
    row = dict.fromkeys(FIELDS)
    row.update(level=path.stem, algorithm=algorithm, repeat=repeat, status="ERROR", error="")
    actions = []
    try:
        board = Board(str(path))
        errors = configuration_errors(board)
        if errors:
            raise ValueError("; ".join(errors))
        options = {"time_limit": args.time_limit, "node_limit": args.node_limit}
        if algorithm == "IDS":
            options["max_depth"] = args.max_depth
        result = SOLVERS[algorithm](board, **options).solve()
        row.update(status=result["status"], expanded_nodes=result["expanded_nodes"],
                   time_ms=result["search_time_sec"] * 1000, memory_kib=result["peak_memory_kib"])
        if result["solved"]:
            actions = result["actions"]
            try:
                row.update(replay_solution(board, actions))
            except Exception as exc:
                row.update(status="INVALID", error=str(exc))
    except Exception as exc:
        row.update(status="ERROR", error=f"{type(exc).__name__}: {exc}")
    return row, actions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--time-limit", type=float, default=10)
    parser.add_argument("--node-limit", type=int, default=250000)
    parser.add_argument("--max-depth", type=int, default=50)
    parser.add_argument("--machine-label", default="")
    args = parser.parse_args()
    if args.repeats < 1 or args.time_limit <= 0 or args.node_limit < 1 or args.max_depth < 0:
        parser.error("Invalid repeat count or search limit")
    paths = sorted((SOURCE / "levels").glob("*.json"))
    if not paths:
        parser.error("No JSON levels found")
    output = SOURCE / "results" / "runs" / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    output.mkdir(parents=True)
    metadata = metadata_for(args, paths)
    metadata_path = output / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Output:", output, flush=True)
    rows = []
    interrupted = False
    total = len(paths) * len(SOLVERS) * args.repeats
    try:
        with (output / "raw.csv").open("w", newline="", encoding="utf-8-sig") as stream, \
             (output / "solutions.jsonl").open("w", encoding="utf-8") as solutions:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            for repeat in range(1, args.repeats + 1):
                algorithms = list(SOLVERS)
                offset = (repeat - 1) % len(algorithms)
                algorithms = algorithms[offset:] + algorithms[:offset]
                for path in paths:
                    for algorithm in algorithms:
                        row, actions = run_case(path, algorithm, repeat, args)
                        rows.append(row)
                        writer.writerow(row)
                        stream.flush()
                        solutions.write(json.dumps({"level": path.stem, "algorithm": algorithm,
                                                    "repeat": repeat, "status": row["status"],
                                                    "actions": actions}, ensure_ascii=False) + "\n")
                        solutions.flush()
                        print(f"[{len(rows)}/{total}] {path.stem} {algorithm} "
                              f"run={repeat} {row['status']} time_ms={row['time_ms']}", flush=True)
    except KeyboardInterrupt:
        interrupted = True
        print("Stopped; completed rows have been saved.", flush=True)
    finally:
        metadata["finished_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        metadata["completed"] = len(rows) == total
        metadata["completed_runs"] = len(rows)
        metadata["expected_runs"] = total
        metadata["successful_runs"] = sum(row["status"] == "OK" for row in rows)
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    issues = export_report(output, rows, [path.stem for path in paths], metadata)
    print("Saved CSV, metadata, LaTeX tables and figures to:", output)
    for issue in issues:
        print("CHECK FAILED:", issue)
    if interrupted:
        return 130
    return int(bool(issues) or any(row["status"] != "OK" for row in rows))


if __name__ == "__main__":
    raise SystemExit(main())
