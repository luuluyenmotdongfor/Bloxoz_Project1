import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ALGORITHMS = ["BFS", "DFS", "IDS", "UCS", "A*"]
COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00"]


def draw_panel(ax, rows, levels, metric, title, unit, multiplier=1):
    width = 0.16
    values = []
    lookup = {(row["level"], row["algorithm"]): row for row in rows}

    for index, (algorithm, color) in enumerate(zip(ALGORITHMS, COLORS)):
        heights = [
            float(lookup[(level, algorithm)][metric]) * multiplier
            for level in levels
        ]
        values.extend(heights)
        positions = [i + (index - 2) * width for i in range(len(levels))]
        ax.bar(positions, heights, width=width, color=color,
               label=algorithm, edgecolor="white", linewidth=0.25)

    positive = [value for value in values if value > 0]
    scale = "linear"
    if positive and max(positive) / min(positive) >= 30:
        scale = "log" if len(positive) == len(values) else "symlog"
        if scale == "log":
            ax.set_yscale("log")
        else:
            ax.set_yscale("symlog", linthresh=min(positive))

    ax.set_title(f"{title} ({scale} scale)", loc="left", fontsize=12)
    ax.set_ylabel(unit)
    ax.set_xticks(range(len(levels)))
    ax.set_xticklabels([level.split("_")[1] for level in levels])
    ax.set_xlabel("Level")
    ax.set_xlim(-0.7, len(levels) - 0.3)
    ax.grid(axis="y", which="major", linestyle="--", alpha=0.35)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def save_figure(rows, levels, panels, destination):
    fig, axes = plt.subplots(len(panels), 1,
                             figsize=(10, 3.25 * len(panels)), squeeze=False)
    for ax, panel in zip(axes[:, 0], panels):
        draw_panel(ax, rows, levels, *panel)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=5,
               frameon=False, bbox_to_anchor=(0.5, 0.995))
    fig.tight_layout(rect=(0, 0, 1, 0.96), h_pad=1.8)
    fig.savefig(destination, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args()

    with args.csv_file.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    if not rows or any(row["status"] != "OK" for row in rows):
        raise ValueError("This plot requires a complete CSV with all rows OK.")
    if any(row["successful_runs"] != row["repeats"] for row in rows):
        raise ValueError("Some repeated runs are missing or unsuccessful.")

    levels = sorted({row["level"] for row in rows})
    expected = {(level, algorithm) for level in levels for algorithm in ALGORITHMS}
    actual = {(row["level"], row["algorithm"]) for row in rows}
    if actual != expected or len(actual) != len(rows):
        raise ValueError("Missing or duplicated level/algorithm results.")

    output = args.csv_file.parent / "overleaf_figures"
    output.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})

    save_figure(rows, levels, [
        ("total_time_sec", "Solver setup and search time", "Time (ms)", 1000),
        ("peak_memory_kib", "Peak Python memory", "Memory (KiB)", 1),
        ("expanded_nodes", "Expanded nodes", "Expansions", 1),
    ], output / "bfs.jpg")

    save_figure(rows, levels, [
        ("solution_length", "Solution length", "Actions", 1),
        ("solution_cost", "Weighted solution cost", "Cost", 1),
    ], output / "solution.jpg")


if __name__ == "__main__":
    main()