# Bloxorz Solver — CSC14003

Python implements the game rules and five search algorithms: BFS, DFS, IDS, UCS and A*.
Flask connects the solvers to the Three.js interface. The dataset contains 20 JSON levels.

## Installation and GUI

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe Source/main.py
```

Open http://127.0.0.1:5000. Arrow keys move the block; Space changes the active cube
after a split. Solve starts from the initial state of the selected level.

## Search behavior

- BFS minimizes the number of actions. DFS does not guarantee an optimal solution.
- IDS repeats depth-limited search up to 50 by default. Its `best_depth` dictionary
  requires additional state storage; memory is not just the recursive path.
- UCS and A* share the cost of the successor state:
  `1 + 2*has_fragile + 2*is_split + 0.1*closed_bridges`.
- Costs are stored as integer tenths to avoid floating-point tie errors.
- A* uses distances in a relaxed cell graph, including all teleport edges. Normal
  grid edges cost 0.5 and directed teleport edges cost 0. The heuristic is the
  minimum distance over occupied cells. Preprocessing occurs inside the timed search.
- UCS/A* discard stale heap entries and accept a better g value even after an
  earlier expansion. Heap ties use insertion order, not `State.__lt__`.
- BFS/DFS/UCS/A* reconstruct actions from parent links instead of copying a full
  path into every frontier entry.
- `expanded_nodes` counts calls to generate successors, including IDS boundary
  checks. Merely checking a goal does not increase this counter.
- Status distinguishes `OK`, `UNSOLVABLE`, `TIME_LIMIT`, `NODE_LIMIT`, and
  `DEPTH_LIMIT`. Invalid returned paths and exceptions are recorded separately.

## Review before benchmarking

These commands are provided for review; adding the files does not run them.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s Source/tests -v
.\.venv\Scripts\python.exe Source/validate_levels.py --coverage
```

The tests cover empty solutions, unsolvable maps, node counting, limits, fragile
Split configuration, multiple teleports, heuristic consistency on a small graph,
and agreement of UCS/A* costs and BFS/IDS lengths on a small example.

The level validator checks configuration, replays BFS solutions and can search
for reachable Split activations. `LIMIT` in coverage means the check was not
completed; `UNREACHABLE` means the reachable state graph was exhausted without
activating every configured Split. A solvable map does not automatically exercise
every mechanism.

## Benchmark after review

```powershell
.\.venv\Scripts\python.exe Source/benchmark.py --repeats 3 --time-limit 10 --node-limit 250000 --machine-label "Lenovo Legion 5 R7000 2024"
```

The label is supplied by the person running the command; CPU, RAM, OS, Python and
GPU information are collected from that computer where available. The solvers
run on the CPU, not CUDA. There is no separate warm-up run. Solver order rotates
between repetitions, while execution remains sequential.

The time limit is checked cooperatively during search. It is not an operating
system hard timeout. The node limit bounds expansion work, not the entire process
RAM. Time, node or depth limits must not be interpreted as proof of no solution.

Each invocation creates `Source/results/runs/<timestamp>/` containing:

- `metadata.json`: hardware, versions, commit, dirty flag, limits and file hashes.
- `raw.csv`: every completed run, including failures and limits.
- `solutions.jsonl`: action sequences for replay and review.
- `summary.csv`: per-level/per-algorithm median and Q1/Q3.
- `checks.json`: disagreement between BFS/IDS lengths or UCS/A* costs.
- `machine_info.tex`, `appendix_results.tex`: tables for the existing report template.
- `time`, `memory`, `nodes`, `length`, `cost`: separate JPG/PDF figures.
- `bfs.jpg`: combined comparison of all five solvers, retaining the report's image filename.
- `chart_scales.json`: recorded linear/log/symlog choice for each metric.

Only cases with all requested repetitions successful are plotted. Limits and
missing results are not replaced by zero. Error bars show Q1–Q3 within a case.
A positive range of at least 30 times selects a logarithmic scale; zero-valued
data use symlog when that range rule applies.

Raw rows are flushed after each run. Ctrl+C preserves completed rows and exports
partial results. The output folder is ignored by Git and does not overwrite the
historical CSV in `Source/results/`. Historical results must not be used as data
for the changed solvers or maps.

## Dataset and report

- 01–03: basic movement.
- 04–06: fragile tiles.
- 07–09: bridges and Soft/Heavy switches.
- 10–12: split/merge with other mechanisms.
- 13–20: additional configurations, including multiple Split switches.

The Split tiles at level 14 `(5,10)`, level 15 `(1,3)` and level 16 `(4,8)` use
ordinary floor, since standing on fragile tiles is rejected before activation.
Coordinates are zero-based. Reachability and complete solutions still need review.

Do not use the old level-05 claim of BFS 8 actions versus UCS 16 actions. The report
must use newly measured lengths and costs. A* and UCS optimize the same cost now;
an optimal weighted solution may contain more actions than a BFS solution.

Keep the original Overleaf template. Update the environment table, graphs, full
results and conclusions only after the reviewed version has been benchmarked.
Retain references to the game, template and assistance as required by the assignment.

## Branch workflow

Work on a separate branch, commit source changes and push that branch for review.
Run the benchmark only after review, using the exact reviewed commit. If changes
are made after measurement, rerun affected experiments and keep the provenance.

Original game: https://www.coolmathgames.com/0-bloxorz
