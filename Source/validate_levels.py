import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from core.board import Board
from solvers.bfs_solver import BFSSolver

def validate_all_levels():
    levels_dir = os.path.join(BASE_DIR, "levels")
    files = sorted([f for f in os.listdir(levels_dir) if f.endswith(".json")])

    print("=" * 95)
    print(f"{'File':<15} | {'Difficulty':<12} | {'Status':<10} | {'Min Moves':<10} | {'Expanded Nodes':<15} | {'Features'}")
    print("=" * 95)

    valid_count = 0
    for f in files:
        path = os.path.join(levels_dir, f)
        try:
            board = Board(path)
            solver = BFSSolver(board)
            res = solver.solve()

            has_fragile = any(2 in row for row in board.grid)
            sw_types = sorted(list({sw["type"] for sw in board.switches.values()}))
            features = []
            if has_fragile:
                features.append("fragile")
            if board.bridge_ids:
                features.append(f"bridges({len(board.bridge_ids)})")
            if sw_types:
                features.append("switches:" + ",".join(sw_types))
            feat_str = ", ".join(features) if features else "basic_only"

            if res["solved"] and res["solution_length"] > 0:
                status = "✅ SOLVABLE"
                valid_count += 1
            else:
                status = "❌ UNSOLVABLE"

            diff = getattr(board, "name", "")[:10]
            print(f"{f:<15} | {diff:<12} | {status:<10} | {res['solution_length']:<10} | {res['expanded_nodes']:<15} | {feat_str}")
        except Exception as e:
            print(f"{f:<15} | {'ERROR':<12} | ❌ CRASH   | {'-':<10} | {'-':<15} | Lỗi JSON: {e}")

    print("=" * 95)
    print(f"Tổng kết: {valid_count}/{len(files)} màn chơi hợp lệ và chắc chắn giải được (Yêu cầu tối thiểu: 10 màn).")

if __name__ == "__main__":
    validate_all_levels()
