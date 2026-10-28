import csv
import json
import math
from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ALGORITHMS = ["BFS", "DFS", "IDS", "UCS", "A*"]
METRICS = {
    "time_ms": ("Search time (ms)", "time"),
    "memory_kib": ("Peak Python memory (KiB)", "memory"),
    "expanded_nodes": ("Successor-generation calls", "nodes"),
    "solution_length": ("Solution length (actions)", "length"),
    "path_cost": ("Total path cost", "cost"),
}


def write_csv(path, rows):
    if rows:
        with Path(path).open("w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def percentile(values, q):
    values = sorted(values)
    position = (len(values) - 1) * q
    lower, upper = math.floor(position), math.ceil(position)
    return values[lower] + (values[upper] - values[lower]) * (position - lower)


def summarize(rows, levels, repeats):
    summary = []
    for level in levels:
        for algorithm in ALGORITHMS:
            group = [r for r in rows if r["level"] == level and r["algorithm"] == algorithm]
            ok = [r for r in group if r["status"] == "OK"]
            complete = len(group) == repeats and len(ok) == repeats
            status = "OK" if complete else "PARTIAL"
            if group and len({r["status"] for r in group}) == 1 and not complete:
                status = group[0]["status"] if group[0]["status"] != "OK" else "PARTIAL"
            record = dict(level=level, algorithm=algorithm, status=status,
                          attempts=len(group), successful_runs=len(ok), expected_runs=repeats)
            for key in list(METRICS) + ["switch_cube_count", "split_count"]:
                values = [r[key] for r in ok]
                for suffix, q in [("median", 0.5), ("q1", 0.25), ("q3", 0.75)]:
                    record[f"{key}_{suffix}"] = percentile(values, q) if complete else None
            summary.append(record)
    return summary


def compare_solvers(summary):
    issues = []
    for level in sorted({r["level"] for r in summary}):
        group = {r["algorithm"]: r for r in summary if r["level"] == level}
        for a, b, metric in [("BFS", "IDS", "solution_length_median"),
                             ("UCS", "A*", "path_cost_median")]:
            if group[a]["status"] == group[b]["status"] == "OK":
                if group[a][metric] != group[b][metric]:
                    issues.append(f"{level}: {a} and {b} disagree on {metric}")
                    group[a]["status"] = group[b]["status"] = "MISMATCH"
        if any(r["status"] == "OK" for r in group.values()):
            for row in group.values():
                if row["status"] == "UNSOLVABLE":
                    issues.append(f"{level}: false UNSOLVABLE from {row['algorithm']}")
                    row["status"] = "MISMATCH"
    return issues


def draw_metric(ax, summary, levels, key):
    values = []
    for row in summary:
        if row["status"] == "OK":
            values.extend(row[f"{key}_{s}"] for s in ["median", "q1", "q3"])
    positive = [v for v in values if v > 0]
    scale = "linear"
    if positive and max(positive) / min(positive) >= 30:
        scale = "symlog" if any(v == 0 for v in values) else "log"
    if scale == "symlog":
        ax.set_yscale("symlog", linthresh=min(positive))
    else:
        ax.set_yscale(scale)
    markers = ["o", "s", "^", "D", "x"]
    for algorithm, marker in zip(ALGORITHMS, markers):
        lookup = {r["level"]: r for r in summary if r["algorithm"] == algorithm}
        y, lower, upper = [], [], []
        for level in levels:
            row = lookup[level]
            if row["status"] != "OK":
                y.append(float("nan")); lower.append(0); upper.append(0)
            else:
                median = row[f"{key}_median"]
                y.append(median)
                lower.append(median - row[f"{key}_q1"])
                upper.append(row[f"{key}_q3"] - median)
        if any(math.isfinite(value) for value in y):
            ax.errorbar(range(len(levels)), y, yerr=[lower, upper], marker=marker,
                        markersize=4, linewidth=1.2, capsize=2, label=algorithm)
    ax.set_xticks(range(len(levels)))
    ax.set_xticklabels([level.split("_")[1] for level in levels])
    ax.set_xlabel("Level")
    ax.set_ylabel(METRICS[key][0])
    ax.set_title(f"{METRICS[key][0]} - {scale} scale")
    ax.grid(True, which="both", linestyle="--", alpha=0.3)
    if ax.get_legend_handles_labels()[0]:
        ax.legend(fontsize=8, ncol=5)
    return scale


def latex_escape(value):
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
                    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in str(value))


def export_tables(output, summary, metadata):
    hardware = metadata["hardware"]
    machine = [
        ("Máy chạy", metadata["machine_label"] or hardware.get("model", "Không xác định")),
        ("CPU", hardware.get("cpu", "Không xác định")),
        ("RAM", hardware.get("ram", "Không xác định")),
        ("GPU", hardware.get("gpu", "Không xác định")),
        ("Hệ điều hành", metadata["os"]),
        ("Python", metadata["python"]),
        ("Thời điểm", metadata["started_at"]),
        ("Commit", metadata["commit"]),
        ("Working tree", "Có thay đổi chưa commit" if metadata["dirty"] else "Sạch"),
        ("Số lần đo mỗi cặp", metadata["repeats"]),
        ("Giới hạn mỗi lần", f"{metadata['time_limit']} s; {metadata['node_limit']} lượt mở rộng"),
        ("Warm-up", "Không thực hiện lượt warm-up riêng"),
        ("Bộ nhớ", "Peak tracemalloc, đơn vị KiB; không phải RAM toàn tiến trình"),
        ("Phạm vi đo", "Tìm kiếm, bao gồm tiền xử lý heuristic; không gồm kiểm chứng lời giải"),
    ]
    lines = [r"\begin{table}[H]", r"\centering", r"\begin{tabular}{|p{4cm}|p{11cm}|}",
             r"\hline", r"\textbf{Thông số} & \textbf{Giá trị} \\ \hline"]
    lines.extend(latex_escape(k) + " & " + latex_escape(v) + r" \\ \hline" for k, v in machine)
    lines += [r"\end{tabular}", r"\caption{Môi trường và cấu hình thực nghiệm}", r"\end{table}"]
    (output / "machine_info.tex").write_text("\n".join(lines), encoding="utf-8")

    codes = {"OK": "OK", "TIME_LIMIT": "T", "NODE_LIMIT": "N", "DEPTH_LIMIT": "D",
             "UNSOLVABLE": "U", "ERROR": "E", "INVALID": "I", "PARTIAL": "P", "MISMATCH": "M"}
    lines = ["OK: đủ các lần đo hợp lệ; T/N/D: hết giới hạn thời gian/nút/độ sâu;",
             "U: không có lời giải; E: lỗi chạy; I: đường đi không hợp lệ;",
             "P: thiếu lần đo hoặc kết quả không đồng nhất; M: không khớp đối chiếu thuật toán.",
             "Các ô không có số liệu được ghi bằng dấu ---."]
    for begin in range(0, len(summary), 10):
        lines += [r"\begin{table}[H]", r"\centering", r"\begin{tabular}{|c|c|c|r|r|r|r|r|}",
                  r"\hline", r"Màn & Bộ giải & TT & $L$ & $C$ & Nút & ms & KiB \\ \hline"]
        for row in summary[begin:begin + 10]:
            cells = [row["level"].split("_")[1], row["algorithm"], codes.get(row["status"], "E")]
            for metric, digits in [("solution_length", 0), ("path_cost", 1), ("expanded_nodes", 0),
                                   ("time_ms", 3), ("memory_kib", 2)]:
                value = row[f"{metric}_median"]
                cells.append(f"{value:.{digits}f}" if row["status"] == "OK" else "---")
            lines.append(" & ".join(latex_escape(cell) for cell in cells) + r" \\ \hline")
        lines += [r"\end{tabular}", r"\caption{Kết quả thực nghiệm: trung vị của các cặp đủ lần đo hợp lệ}",
                  r"\end{table}"]
    (output / "appendix_results.tex").write_text("\n".join(lines), encoding="utf-8")


def export_report(output, rows, levels, metadata):
    summary = summarize(rows, levels, metadata["repeats"])
    issues = compare_solvers(summary)
    write_csv(output / "summary.csv", summary)
    (output / "checks.json").write_text(json.dumps(issues, ensure_ascii=False, indent=2), encoding="utf-8")
    export_tables(output, summary, metadata)
    scales = {}
    for key, (_, filename) in METRICS.items():
        fig, ax = plt.subplots(figsize=(12, 5))
        scales[key] = draw_metric(ax, summary, levels, key)
        fig.tight_layout()
        fig.savefig(output / f"{filename}.jpg", dpi=220)
        fig.savefig(output / f"{filename}.pdf")
        plt.close(fig)
    fig, axes = plt.subplots(3, 2, figsize=(16, 15))
    for ax, key in zip(axes.flat, METRICS):
        draw_metric(ax, summary, levels, key)
    axes.flat[-1].axis("off")
    axes.flat[-1].text(0.05, 0.8, "Median with Q1-Q3 error bars.\nOnly fully successful cases are plotted.\n"
                     "Missing/limited cases remain blank.\nLog scale is used when the positive range is >= 30x.",
                     transform=axes.flat[-1].transAxes, va="top", fontsize=12)
    fig.tight_layout()
    fig.savefig(output / "bfs.jpg", dpi=220)
    plt.close(fig)
    (output / "chart_scales.json").write_text(json.dumps(scales, indent=2), encoding="utf-8")
    return issues
