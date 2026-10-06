from __future__ import annotations

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import pandas as pd

from .data_processing import grade_distribution

NAVY = "#18324B"
BLUE = "#3976A8"
TEAL = "#2C8C83"
MUTED = "#708090"
GRID = "#E6ECF1"
GRADE_COLORS = ["#2C8C83", "#4B9A82", "#7FA66A", "#B3A95D", "#D29A54", "#D47D5F", "#C65B5B"]


def _style_axes(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.set_facecolor("#FFFFFF")
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(axis="both", colors=MUTED, labelsize=14, length=0, pad=5)
    ax.title.set_color(NAVY)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


def _finish(fig: Figure, ax: plt.Axes, grid_axis: str = "y") -> Figure:
    _style_axes(ax, grid_axis)
    fig.patch.set_facecolor("#FFFFFF")
    fig.tight_layout(pad=2.0)
    return fig


def grade_chart(df: pd.DataFrame) -> Figure:
    counts = grade_distribution(df)
    fig, ax = plt.subplots(figsize=(12, 4.2), dpi=110)
    bars = ax.bar(counts.index, counts.values, color=GRADE_COLORS, width=0.66)
    ax.bar_label(bars, padding=4, color=NAVY, fontsize=14)
    ax.set_title("Students by grade", loc="left", fontsize=21, fontweight="bold", pad=12)
    ax.set_xlabel("Grade", fontsize=16, labelpad=8)
    ax.set_ylabel("Number of students", fontsize=16, labelpad=8)
    ax.set_ylim(0, max(1.2, float(counts.max()) * 1.18))
    ax.grid(axis="x", visible=False)
    return _finish(fig, ax)


def subject_chart(df: pd.DataFrame) -> Figure:
    averages = df.groupby("subject")["percentage"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(12, 4.2), dpi=110)
    bars = ax.barh(averages.index, averages.values, color=BLUE, height=0.62)
    ax.bar_label(bars, fmt="%.1f%%", padding=4, color=NAVY, fontsize=13)
    ax.set_title("Average result by subject", loc="left", fontsize=21, fontweight="bold", pad=12)
    ax.set_xlabel("Average percentage", fontsize=16, labelpad=8)
    ax.set_xlim(0, min(110, max(100, float(averages.max()) + 12)))
    ax.set_ylabel("")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.grid(axis="y", visible=False)
    return _finish(fig, ax, grid_axis="x")


def semester_chart(df: pd.DataFrame) -> Figure:
    student_results = df.groupby(["semester", "student_id"])["percentage"].mean()
    averages = student_results.groupby(level="semester").mean()
    fig, ax = plt.subplots(figsize=(12, 4.2), dpi=110)
    ax.plot(averages.index, averages.values, marker="o", markersize=7, linewidth=2.5, color=TEAL)
    for semester, average in averages.items():
        ax.annotate(f"{average:.1f}%", (semester, average), xytext=(0, 9), textcoords="offset points",
                    ha="center", color=NAVY, fontsize=14)
    ax.set_title("Average subject result across semesters", loc="left", fontsize=21, fontweight="bold", pad=12)
    ax.set_xlabel("Semester", fontsize=16, labelpad=8)
    ax.set_ylabel("Average percentage", fontsize=16, labelpad=8)
    ax.set_ylim(0, 110)
    ax.grid(axis="x", visible=False)
    return _finish(fig, ax)


def histogram_chart(df: pd.DataFrame) -> Figure:
    fig, ax = plt.subplots(figsize=(12, 4.2), dpi=110)
    ax.hist(df["percentage"], bins=range(0, 101, 10), color=BLUE, edgecolor="#FFFFFF", linewidth=1.5)
    ax.set_title("How subject results are distributed", loc="left", fontsize=21, fontweight="bold", pad=12)
    ax.set_xlabel("Subject result (%)", fontsize=16, labelpad=8)
    ax.set_ylabel("Number of subject results", fontsize=16, labelpad=8)
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 10))
    ax.grid(axis="x", visible=False)
    return _finish(fig, ax)


def scatter_chart(df: pd.DataFrame) -> Figure:
    student_results = df.groupby("student_id").agg(
        attendance=("attendance", "mean"),
        percentage=("percentage", "mean"),
    )
    fig, ax = plt.subplots(figsize=(12, 4.2), dpi=110)
    ax.scatter(student_results["attendance"], student_results["percentage"], alpha=0.72, s=48, color=BLUE,
               edgecolors="#FFFFFF", linewidths=0.7)
    ax.set_title("Attendance and student average", loc="left", fontsize=21, fontweight="bold", pad=12)
    ax.set_xlabel("Attendance (%)", fontsize=16, labelpad=8)
    ax.set_ylabel("Student average (%)", fontsize=16, labelpad=8)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.grid(color=GRID, linewidth=0.8)
    return _finish(fig, ax, grid_axis="both")
