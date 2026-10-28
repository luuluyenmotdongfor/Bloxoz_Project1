import argparse
import time
from collections import deque
from pathlib import Path
from core.board import Board
from core.state import Orientation
from solvers.bfs_solver import BFSSolver
from validation import configuration_errors, replay_solution


def split_coverage(board, seconds, node_limit):
    expected = {cell for cell, switch in board.switches.items() if switch["type"] == "split"}
    reached = set()
    start = board.get_initial_state()
    queue, seen = deque([start]), {start}
    deadline, expanded = time.perf_counter() + seconds, 0
    while queue and reached != expected:
        if time.perf_counter() >= deadline or expanded >= node_limit:
            return "LIMIT", sorted(reached), sorted(expected - reached)
        state = queue.popleft()
        expanded += 1
        for action, next_state in board.get_successors(state):
            if state.orientation != Orientation.SPLIT and next_state.orientation == Orientation.SPLIT:
                intermediate = board._apply_move(state, action)
                reached.add((intermediate.r, intermediate.c))
            if next_state not in seen:
                seen.add(next_state)
                queue.append(next_state)
    status = "ALL_REACHED" if reached == expected else "UNREACHABLE"
    return status, sorted(reached), sorted(expected - reached)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--time-limit", type=float, default=10)
    parser.add_argument("--node-limit", type=int, default=250000)
    args = parser.parse_args()
    if args.time_limit <= 0 or args.node_limit < 1:
        parser.error("Search limits must be positive")
    failures = 0
    for path in sorted((Path(__file__).parent / "levels").glob("*.json")):
        try:
            board = Board(str(path))
            errors = configuration_errors(board)
            if errors:
                raise ValueError("; ".join(errors))
            result = BFSSolver(board, args.time_limit, args.node_limit).solve()
            details = replay_solution(board, result["actions"]) if result["solved"] else {}
            print(path.name, result["status"], details)
            if result["status"] != "OK":
                failures += 1
            if args.coverage:
                status, reached, missing = split_coverage(board, args.time_limit, args.node_limit)
                print("  Split coverage:", status, "reached=", reached, "missing=", missing)
                if status != "ALL_REACHED":
                    failures += 1
        except Exception as exc:
            failures += 1
            print(path.name, "ERROR", str(exc))
    return int(failures > 0)


if __name__ == "__main__":
    raise SystemExit(main())
