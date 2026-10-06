from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "student_id", "name", "semester", "section", "subject",
    "marks", "max_marks", "attendance"
]


def load_results(path: str | Path) -> pd.DataFrame:
    """Read and validate a result CSV."""
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return clean_results(df)


def clean_results(df: pd.DataFrame) -> pd.DataFrame:
    """Clean raw rows and derive subject percentage and grade."""
    out = df.copy()
    for col in ["marks", "max_marks", "attendance"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["marks"] = out["marks"].fillna(0).clip(lower=0)
    out["max_marks"] = out["max_marks"].fillna(100).replace(0, 100).clip(lower=1)
    out["attendance"] = out["attendance"].fillna(0).clip(lower=0, upper=100)
    out["semester"] = out["semester"].fillna("Unknown").astype(str)
    out["section"] = out["section"].fillna("Unknown").astype(str)
    out["percentage"] = (out["marks"] / out["max_marks"] * 100).clip(0, 100)
    out["grade"] = out["percentage"].apply(grade_from_percentage)
    out["passed"] = out["percentage"] >= 40
    return out


def grade_from_percentage(pct: float) -> str:
    if pd.isna(pct):
        return "F"
    if pct >= 90:
        return "A+"
    if pct >= 80:
        return "A"
    if pct >= 70:
        return "B"
    if pct >= 60:
        return "C"
    if pct >= 50:
        return "D"
    if pct >= 40:
        return "E"
    return "F"


def student_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate subject rows into one row per student/semester."""
    grouped = (
        df.groupby(["student_id", "name", "semester", "section"], as_index=False)
        .agg(
            subjects=("subject", "nunique"),
            total_marks=("marks", "sum"),
            total_max_marks=("max_marks", "sum"),
            percentage=("percentage", "mean"),
            attendance=("attendance", "mean"),
            passed_subjects=("passed", "sum"),
        )
    )
    grouped["passed"] = grouped["passed_subjects"] == grouped["subjects"]
    grouped["grade"] = grouped["percentage"].apply(grade_from_percentage)
    return grouped.sort_values(["semester", "percentage"], ascending=[True, False])


def student_overview(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate selected subject rows into one performance record per student."""
    columns = ["student_id", "name", "subjects", "percentage", "attendance",
               "failed_subjects", "passed", "grade"]
    if df.empty:
        return pd.DataFrame(columns=columns)
    overview = (
        df.groupby("student_id", as_index=False)
        .agg(
            name=("name", "first"),
            subjects=("subject", "nunique"),
            percentage=("percentage", "mean"),
            attendance=("attendance", "mean"),
            failed_subjects=("passed", lambda passed: int((~passed).sum())),
            passed=("passed", "all"),
        )
    )
    overview["grade"] = overview["percentage"].apply(grade_from_percentage)
    return overview.sort_values("percentage", ascending=False)


def kpis(df: pd.DataFrame) -> dict[str, float | int]:
    """Return dashboard-level metrics."""
    overview = student_overview(df)
    if overview.empty:
        return {"students": 0, "passed": 0, "average": 0.0, "pass_rate": 0.0, "top": 0.0}
    return {
        "students": int(len(overview)),
        "passed": int(overview["passed"].sum()),
        "average": float(overview["percentage"].mean()),
        "pass_rate": float(overview["passed"].mean() * 100),
        "top": float(overview["percentage"].max()),
    }


def subject_averages(df: pd.DataFrame) -> pd.Series:
    return df.groupby("subject")["percentage"].mean().sort_values(ascending=False)


def grade_distribution(df: pd.DataFrame) -> pd.Series:
    order = ["A+", "A", "B", "C", "D", "E", "F"]
    return student_overview(df)["grade"].value_counts().reindex(order, fill_value=0)
