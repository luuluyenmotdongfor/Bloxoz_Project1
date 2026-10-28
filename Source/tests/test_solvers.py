import json
import sys
import tempfile
import unittest
from collections import deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.board import Board
from core.state import State, Orientation
from solvers.bfs_solver import BFSSolver
from solvers.dfs_solver import DFSSolver
from solvers.ids_solver import IDSSolver
from solvers.ucs_solver import UCSSolver
from solvers.astar_solver import AStarSolver
from solvers.search_utils import RelaxedHeuristic, step_cost_units
from validation import configuration_errors, replay_solution

SOLVERS = [BFSSolver, DFSSolver, IDSSolver, UCSSolver, AStarSolver]


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)

    def board(self, grid, start, goal, **extra):
        path = Path(self.directory.name) / "level.json"
        data = dict(grid=grid, start=start, goal=goal, **extra)
        path.write_text(json.dumps(data), encoding="utf-8")
        return Board(str(path))

    def test_start_is_goal(self):
        board = self.board([[1]], [0, 0], [0, 0])
        for cls in SOLVERS:
            with self.subTest(solver=cls.__name__):
                result = cls(board).solve()
                self.assertEqual(result["status"], "OK")
                self.assertEqual(result["actions"], [])
                self.assertEqual(result["expanded_nodes"], 0)

    def test_unsolvable(self):
        board = self.board([[1, 0, 1]], [0, 0], [0, 2])
        for cls in SOLVERS:
            with self.subTest(solver=cls.__name__):
                result = cls(board).solve()
                self.assertEqual(result["status"], "UNSOLVABLE")
                self.assertFalse(result["solved"])

    def test_solution_and_node_counter(self):
        for cls in SOLVERS:
            with self.subTest(solver=cls.__name__):
                board = self.board([[1, 1, 1, 1]], [0, 0], [0, 3])
                calls = []
                original = board.get_successors

                def counted(state):
                    calls.append(state)
                    return original(state)

                board.get_successors = counted
                result = cls(board).solve()
                self.assertEqual(result["status"], "OK")
                self.assertEqual(result["expanded_nodes"], len(calls))
                self.assertGreater(len(calls), 0)
                self.assertEqual(replay_solution(board, result["actions"])["solution_length"], 2)

    def test_limits_are_not_unsolvable(self):
        board = self.board([[1, 1, 1, 1]], [0, 0], [0, 3])
        self.assertEqual(IDSSolver(board, max_depth=1).solve()["status"], "DEPTH_LIMIT")
        self.assertEqual(BFSSolver(board, node_limit=1).solve()["status"], "NODE_LIMIT")

    def test_split_configuration(self):
        switch = {"pos": [0, 1], "type": "split", "teleport_to": [[0, 0], [0, 3]]}
        board = self.board([[1, 2, 1, 1]], [0, 0], [0, 3], switches=[switch])
        self.assertTrue(any("fragile" in error for error in configuration_errors(board)))
        board.grid[0][1] = 1
        self.assertEqual(configuration_errors(board), [])

    def test_multiple_teleports(self):
        switches = [
            {"pos": [0, 2], "type": "split", "teleport_to": [[0, 6], [0, 4]]},
            {"pos": [0, 6], "type": "split", "teleport_to": [[0, 8], [0, 1]]},
        ]
        board = self.board([[1] * 9], [0, 0], [0, 8], switches=switches)
        heuristic = RelaxedHeuristic(board)
        self.assertEqual(heuristic(board.get_initial_state()), 10)
        queue = deque([board.get_initial_state()])
        seen = set(queue)
        while queue:
            state = queue.popleft()
            if board.is_goal(state):
                self.assertEqual(heuristic(state), 0)
            for _, target in board.get_successors(state):
                self.assertLessEqual(heuristic(state), step_cost_units(board, target) + heuristic(target))
                if target not in seen:
                    seen.add(target)
                    queue.append(target)

    def test_level_10_teleport_edge(self):
        path = Path(__file__).resolve().parents[1] / "levels" / "level_10.json"
        board = Board(str(path))
        state = State(1, 3, Orientation.LYING_H, board.initial_bridges_mask)
        target = dict(board.get_successors(state))["RIGHT"]
        self.assertEqual(target.orientation, Orientation.SPLIT)
        heuristic = RelaxedHeuristic(board)
        self.assertLessEqual(heuristic(state), step_cost_units(board, target) + heuristic(target))

    def test_ucs_astar_cost_and_bfs_ids_length(self):
        board = self.board([[1] * 7, [1, 2, 2, 1, 1, 1, 1], [1] * 7], [1, 0], [1, 6])
        results = {cls.__name__: cls(board).solve() for cls in SOLVERS}
        for result in results.values():
            self.assertEqual(result["status"], "OK")
        ucs = replay_solution(board, results["UCSSolver"]["actions"])
        astar = replay_solution(board, results["AStarSolver"]["actions"])
        self.assertEqual(ucs["path_cost"], astar["path_cost"])
        self.assertEqual(results["BFSSolver"]["solution_length"], results["IDSSolver"]["solution_length"])


if __name__ == "__main__":
    unittest.main()
