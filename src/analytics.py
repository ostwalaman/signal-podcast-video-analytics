"""KPI querying, opportunity scoring, and statistical experiment analysis."""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import norm
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from src.data_pipeline import DB_PATH, ensure_database


def query(sql: str, params: list | None = None, db_path: Path = DB_PATH) -> pd.DataFrame:
    ensure_database(db_path)
    with duckdb.connect(str(db_path), read_only=True) as con:
        return con.execute(sql, params or []).df()


def load_daily(db_path: Path = DB_PATH) -> pd.DataFrame:
    return query("SELECT * FROM daily_kpis ORDER BY date", db_path=db_path)


def load_creators(db_path: Path = DB_PATH) -> pd.DataFrame:
    return query("SELECT * FROM creator_performance ORDER BY audience_growth_rate DESC", db_path=db_path)


def load_content_performance(db_path: Path = DB_PATH) -> pd.DataFrame:
    return query("SELECT * FROM content_performance", db_path=db_path)


def filter_daily(
    daily: pd.DataFrame,
    markets: list[str],
    categories: list[str],
    formats: list[str],
    start_date,
    end_date,
) -> pd.DataFrame:
    dates = pd.to_datetime(daily["date"])
    return daily[
        daily["market"].isin(markets)
        & daily["category"].isin(categories)
        & daily["format"].isin(formats)
        & dates.between(pd.Timestamp(start_date), pd.Timestamp(end_date))
    ].copy()


def headline_kpis(frame: pd.DataFrame) -> dict[str, float]:
    starts = frame["starts"].sum()
    audience = frame["active_audience"].sum()
    return {
        "active_audience": float(audience),
        "engagement_hours": float(frame["consumed_minutes"].sum() / 60),
        "completion_rate": float(frame["completions"].sum() / starts) if starts else 0,
        "repeat_rate": float(frame["repeat_consumers"].sum() / audience) if audience else 0,
        "video_adoption": float(
            frame.loc[frame["format"] == "Video", "starts"].sum() / starts
        ) if starts else 0,
    }


def category_opportunities(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()
    midpoint = pd.to_datetime(frame["date"]).min() + (
        pd.to_datetime(frame["date"]).max() - pd.to_datetime(frame["date"]).min()
    ) / 2
    work = frame.assign(period=np.where(pd.to_datetime(frame["date"]) <= midpoint, "prior", "current"))
    grouped = (
        work.groupby(["category", "period"], as_index=False)
        .agg(
            starts=("starts", "sum"),
            completions=("completions", "sum"),
            audience=("active_audience", "sum"),
            minutes=("consumed_minutes", "sum"),
        )
    )
    pivot = grouped.pivot(index="category", columns="period", values=["starts", "audience", "minutes"]).fillna(0)
    output = pd.DataFrame(index=pivot.index)
    for metric in ["starts", "audience", "minutes"]:
        current = pivot[(metric, "current")] if (metric, "current") in pivot else 0
        prior = pivot[(metric, "prior")] if (metric, "prior") in pivot else 0
        output[f"{metric}_current"] = current
        output[f"{metric}_growth"] = (current - prior) / np.maximum(prior, 1)
    totals = frame.groupby("category").agg(starts=("starts", "sum"), completions=("completions", "sum"), minutes=("consumed_minutes", "sum"), audience=("active_audience", "sum"))
    output["completion_rate"] = totals["completions"] / totals["starts"]
    output["hours_per_1k_audience"] = totals["minutes"] / 60 / totals["audience"] * 1000
    output["audience_share"] = totals["audience"] / totals["audience"].sum()
    for col in ["starts_growth", "hours_per_1k_audience", "audience_share"]:
        low, high = output[col].min(), output[col].max()
        output[f"{col}_norm"] = (output[col] - low) / (high - low) if high > low else 0.5
    output["opportunity_score"] = 100 * (
        0.4 * output["starts_growth_norm"]
        + 0.4 * output["hours_per_1k_audience_norm"]
        + 0.2 * output["audience_share_norm"]
    )
    return output.reset_index().sort_values("opportunity_score", ascending=False)


def _diff_ci(control: np.ndarray, treatment: np.ndarray, z: float = 1.96) -> tuple[float, float, float]:
    diff = float(treatment.mean() - control.mean())
    se = np.sqrt(control.var(ddof=1) / len(control) + treatment.var(ddof=1) / len(treatment))
    return diff, diff - z * se, diff + z * se


def experiment_summary(db_path: Path = DB_PATH) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    exp = query("SELECT * FROM experiment", db_path=db_path)
    control = exp[exp.assignment == "control"]
    treatment = exp[exp.assignment == "treatment"]
    metrics = []
    for column, label in [
        ("full_episode_discovered", "Full-episode discovery rate"),
        ("full_episode_completed", "Completion rate"),
        ("post_period_minutes", "Listening minutes per user"),
    ]:
        diff, low, high = _diff_ci(control[column].to_numpy(), treatment[column].to_numpy())
        metrics.append(
            {
                "metric": label,
                "control": control[column].mean(),
                "treatment": treatment[column].mean(),
                "absolute_lift": diff,
                "relative_lift": diff / control[column].mean(),
                "ci_low": low,
                "ci_high": high,
                "significant": low > 0 or high < 0,
            }
        )
    baseline = float(control.full_episode_discovered.mean())
    target = baseline + 0.02
    effect = proportion_effectsize(target, baseline)
    required_per_group = int(np.ceil(NormalIndPower().solve_power(effect, power=0.8, alpha=0.05)))
    balance = {
        "control_n": len(control),
        "treatment_n": len(treatment),
        "pre_minutes_delta": float(treatment.pre_period_minutes.mean() - control.pre_period_minutes.mean()),
        "required_per_group": required_per_group,
    }
    segments = (
        exp.groupby(["market", "assignment"])["full_episode_discovered"]
        .agg(["mean", "count"])
        .reset_index()
        .pivot(index="market", columns="assignment", values=["mean", "count"])
    )
    segment_output = pd.DataFrame(
        {
            "market": segments.index,
            "control_rate": segments[("mean", "control")],
            "treatment_rate": segments[("mean", "treatment")],
            "control_n": segments[("count", "control")],
            "treatment_n": segments[("count", "treatment")],
        }
    ).reset_index(drop=True)
    segment_output["absolute_lift"] = segment_output.treatment_rate - segment_output.control_rate
    segment_output["standard_error"] = np.sqrt(
        segment_output.control_rate * (1 - segment_output.control_rate) / segment_output.control_n
        + segment_output.treatment_rate * (1 - segment_output.treatment_rate) / segment_output.treatment_n
    )
    segment_output["ci_low"] = segment_output.absolute_lift - 1.96 * segment_output.standard_error
    segment_output["ci_high"] = segment_output.absolute_lift + 1.96 * segment_output.standard_error
    segment_output["significant"] = segment_output.ci_low > 0
    return pd.DataFrame(metrics), balance, segment_output.sort_values("absolute_lift", ascending=False)
