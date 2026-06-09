"""Grounded strategy brief generation from computed metrics only."""

from __future__ import annotations

import json

import pandas as pd


def build_evidence_register(
    opportunities: pd.DataFrame,
    experiment_metrics: pd.DataFrame,
    headline: dict[str, float],
) -> pd.DataFrame:
    """Create a traceable register for every metric used in the strategy brief."""
    rows = [
        {
            "evidence_id": "EXP-PRIMARY",
            "metric": "Full-episode discovery relative lift",
            "value": float(experiment_metrics.iloc[0]["relative_lift"]),
            "display_value": f"{experiment_metrics.iloc[0]['relative_lift']:.1%}",
            "source": "experiment_summary",
        },
        {
            "evidence_id": "EXP-CI",
            "metric": "Full-episode discovery absolute lift 95% CI",
            "value": json.dumps(
                [float(experiment_metrics.iloc[0]["ci_low"]), float(experiment_metrics.iloc[0]["ci_high"])]
            ),
            "display_value": (
                f"{experiment_metrics.iloc[0]['ci_low']:.1%} to "
                f"{experiment_metrics.iloc[0]['ci_high']:.1%}"
            ),
            "source": "experiment_summary",
        },
        {
            "evidence_id": "KPI-HOURS",
            "metric": "Engagement hours",
            "value": float(headline["engagement_hours"]),
            "display_value": f"{headline['engagement_hours']:,.0f}",
            "source": "headline_kpis",
        },
        {
            "evidence_id": "KPI-COMPLETION",
            "metric": "Completion rate",
            "value": float(headline["completion_rate"]),
            "display_value": f"{headline['completion_rate']:.1%}",
            "source": "headline_kpis",
        },
        {
            "evidence_id": "KPI-VIDEO",
            "metric": "Video adoption",
            "value": float(headline["video_adoption"]),
            "display_value": f"{headline['video_adoption']:.1%}",
            "source": "headline_kpis",
        },
        {
            "evidence_id": "KPI-REPEAT",
            "metric": "Repeat consumption rate",
            "value": float(headline["repeat_rate"]),
            "display_value": f"{headline['repeat_rate']:.1%}",
            "source": "headline_kpis",
        },
    ]
    for rank, (_, opportunity) in enumerate(opportunities.head(3).iterrows(), start=1):
        rows.extend(
            [
                {
                    "evidence_id": f"OPP-{rank}-SCORE",
                    "metric": f"{opportunity['category']} opportunity score",
                    "value": float(opportunity["opportunity_score"]),
                    "display_value": f"{opportunity['opportunity_score']:.0f}/100",
                    "source": "category_opportunities",
                },
                {
                    "evidence_id": f"OPP-{rank}-GROWTH",
                    "metric": f"{opportunity['category']} start growth",
                    "value": float(opportunity["starts_growth"]),
                    "display_value": f"{opportunity['starts_growth']:.1%}",
                    "source": "category_opportunities",
                },
                {
                    "evidence_id": f"OPP-{rank}-COMPLETION",
                    "metric": f"{opportunity['category']} completion rate",
                    "value": float(opportunity["completion_rate"]),
                    "display_value": f"{opportunity['completion_rate']:.1%}",
                    "source": "category_opportunities",
                },
            ]
        )
    return pd.DataFrame(rows)


def generate_strategy_brief(
    opportunities: pd.DataFrame,
    experiment_metrics: pd.DataFrame,
    headline: dict[str, float],
) -> str:
    top = opportunities.head(3).reset_index(drop=True)
    discovery = experiment_metrics.iloc[0]
    decision = "SHIP with a measured rollout" if discovery["ci_low"] > 0 else "DO NOT SHIP broadly"
    lines = [
        "## Executive recommendation",
        f"**{decision}.** The video-clips promotion produced a "
        f"**{discovery['relative_lift']:.1%} relative lift** in full-episode discovery "
        f"(95% CI: {discovery['ci_low']:.1%} to {discovery['ci_high']:.1%} absolute). "
        "[EXP-PRIMARY, EXP-CI]",
        "",
        "## Priority investments",
    ]
    for idx, row in top.iterrows():
        lines.append(
            f"{idx + 1}. **{row['category']}** — opportunity score **{row['opportunity_score']:.0f}/100**, "
            f"start growth **{row['starts_growth']:.1%}**, completion **{row['completion_rate']:.1%}**. "
            f"Test increased promotion and creator programming support. "
            f"[OPP-{idx + 1}-SCORE, OPP-{idx + 1}-GROWTH, OPP-{idx + 1}-COMPLETION]"
        )
    lines.extend(
        [
            "",
            "## Portfolio signals",
            f"- Selected content generated **{headline['engagement_hours']:,.0f} engagement hours** "
            f"with a **{headline['completion_rate']:.1%} completion rate**. [KPI-HOURS, KPI-COMPLETION]",
            f"- Video accounted for **{headline['video_adoption']:.1%} of starts**; repeat consumption was "
            f"**{headline['repeat_rate']:.1%}**. [KPI-VIDEO, KPI-REPEAT]",
            "",
            "## Follow-up measurement",
            "- Run a market-stratified rollout with full-episode discovery as the primary metric.",
            "- Monitor listening minutes per user as a guardrail and completion as a secondary metric.",
            "- Test category-specific creative and placement treatments for the highest-ranked opportunities.",
            "",
            "## Limitations",
            "- Behavioral and experiment events are synthetic and intended to demonstrate analytical methodology.",
            "- Opportunity scores are directional and combine normalized growth, intensity, and audience scale.",
            "- Recommendations should be validated using production data and stakeholder context before investment.",
        ]
    )
    return "\n".join(lines)
