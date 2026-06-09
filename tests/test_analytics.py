from pathlib import Path
import re

import duckdb
import numpy as np
import pandas as pd

from src.analytics import category_opportunities, experiment_summary, headline_kpis
from src.data_pipeline import build_database, generate_experiment
from src.strategy import build_evidence_register, generate_strategy_brief


def test_headline_kpis_manual_example():
    frame = pd.DataFrame(
        {
            "starts": [100, 50],
            "completions": [60, 25],
            "active_audience": [80, 40],
            "repeat_consumers": [24, 8],
            "consumed_minutes": [3000, 1200],
            "format": ["Video", "Audio"],
        }
    )
    result = headline_kpis(frame)
    assert result["completion_rate"] == 85 / 150
    assert result["engagement_hours"] == 70
    assert result["video_adoption"] == 100 / 150


def test_experiment_is_reproducible_and_balanced():
    first = generate_experiment(np.random.default_rng(42), count=4000)
    second = generate_experiment(np.random.default_rng(42), count=4000)
    pd.testing.assert_frame_equal(first, second)
    assert first.assignment.value_counts().to_dict() == {"control": 2000, "treatment": 2000}


def test_database_views_and_experiment_lift(tmp_path: Path):
    db_path = build_database(tmp_path / "test.duckdb")
    with duckdb.connect(str(db_path), read_only=True) as con:
        views = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        assert {"daily_kpis", "content_performance", "creator_performance"}.issubset(views)
        assert con.execute("SELECT COUNT(*) FROM engagement").fetchone()[0] > 10_000
    metrics, balance, segments = experiment_summary(db_path)
    assert balance["control_n"] == balance["treatment_n"]
    assert metrics.iloc[0].absolute_lift > 0
    assert len(segments) == 5
    assert (segments.ci_low < segments.absolute_lift).all()
    assert (segments.ci_high > segments.absolute_lift).all()


def test_opportunities_and_brief_are_grounded():
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-01-01", "2026-02-01"] * 2),
            "category": ["Tech", "Tech", "News", "News"],
            "starts": [100, 150, 100, 105],
            "completions": [60, 100, 70, 72],
            "active_audience": [80, 120, 80, 82],
            "consumed_minutes": [3000, 5000, 4000, 4200],
        }
    )
    opportunities = category_opportunities(frame)
    metrics = pd.DataFrame(
        [{"relative_lift": 0.1, "ci_low": 0.01, "ci_high": 0.03}]
    )
    headline = {"engagement_hours": 100, "completion_rate": 0.6, "video_adoption": 0.4, "repeat_rate": 0.2}
    brief = generate_strategy_brief(opportunities, metrics, headline)
    evidence = build_evidence_register(opportunities, metrics, headline)
    assert opportunities.iloc[0].category == "Tech"
    assert "Tech" in brief
    assert "synthetic" in brief.lower()
    assert "[EXP-PRIMARY, EXP-CI]" in brief
    assert evidence.evidence_id.is_unique
    assert set(["EXP-PRIMARY", "KPI-HOURS", "OPP-1-SCORE"]).issubset(set(evidence.evidence_id))
    cited_ids = {
        evidence_id.strip()
        for citation in re.findall(r"\[([A-Z0-9,\- ]+)\]", brief)
        for evidence_id in citation.split(",")
    }
    assert cited_ids == set(evidence.evidence_id)
