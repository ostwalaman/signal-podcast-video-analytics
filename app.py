"""Streamlit dashboard for the Podcast & Video Analytics Intelligence Platform."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import (
    category_opportunities,
    experiment_summary,
    filter_daily,
    headline_kpis,
    load_content_performance,
    load_creators,
    load_daily,
)
from src.data_pipeline import ensure_database
from src.strategy import build_evidence_register, generate_strategy_brief

st.set_page_config(
    page_title="Signal · Podcast & Video Intelligence",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

GREEN = "#1ED760"
BG = "#000000"
PANEL = "#181818"
TEXT = "#FFFFFF"
MUTED = "#B3B3B3"
GRID = "#333333"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {{ font-family: 'DM Sans', sans-serif; }}
    .stApp {{ background: {BG}; color: {TEXT}; }}
    [data-testid="stHeader"] {{ display: none; }}
    [data-testid="stSidebar"] {{
        background: #000000;
        border-right: 1px solid #242424;
        min-width: 260px;
    }}
    [data-testid="stSidebar"] * {{ color: {TEXT}; }}
    [data-testid="stSidebar"] [role="radiogroup"] {{ gap: 5px; }}
    [data-testid="stSidebar"] [role="radiogroup"] label {{
        border-radius: 7px;
        padding: 8px 10px;
        transition: background .15s ease, color .15s ease;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: #1A1A1A; }}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
        background: #282828;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {{
        color: {GREEN} !important;
        font-weight: 700;
    }}
    [data-testid="stSidebar"] [role="radiogroup"] [data-testid="stMarkdownContainer"] p {{
        font-size: .93rem;
        font-weight: 600;
    }}
    [data-testid="stMetric"] {{
        background: {PANEL};
        border: 1px solid #292929;
        border-radius: 8px;
        padding: 18px 20px;
        min-height: 108px;
        transition: background .2s ease, transform .2s ease;
    }}
    [data-testid="stMetric"]:hover {{ background: #242424; transform: translateY(-2px); }}
    [data-testid="stMetricLabel"] {{ color: {MUTED}; font-size: 13px; font-weight: 600; }}
    [data-testid="stMetricValue"] {{ color: {TEXT}; font-weight: 800; letter-spacing: -.04em; }}
    [data-testid="stMetricDelta"] svg {{ display: none; }}
    [data-testid="stMetricDelta"] {{ color: {GREEN}; }}
    [data-testid="stPlotlyChart"] {{
        background: {PANEL};
        border: 1px solid #292929;
        border-radius: 8px;
        overflow: hidden;
    }}
    [data-testid="stDataFrame"] {{
        border: 1px solid #292929;
        border-radius: 8px;
        overflow: hidden;
    }}
    .block-container {{
        max-width: 1380px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}
    [data-testid="stVerticalBlock"] {{ gap: 1rem; }}
    [data-testid="column"] > [data-testid="stVerticalBlock"] {{ gap: .75rem; }}
    h1, h2, h3 {{ color: {TEXT}; letter-spacing: -0.03em; }}
    h1 {{
        font-size: 2.55rem !important; font-weight: 800 !important;
        line-height: 1.08 !important; margin: 0 !important;
    }}
    h2 {{ margin: 1.5rem 0 .25rem !important; font-weight: 800 !important; }}
    h3 {{ margin: 1.15rem 0 .25rem !important; font-weight: 700 !important; }}
    p, li {{ color: #D4D4D4; }}
    .signal-brand {{
        display: flex; align-items: center; gap: 10px;
        font-size: 1.45rem; font-weight: 800; color: {TEXT};
        margin: .25rem 0 1.5rem;
        letter-spacing: -.04em;
    }}
    .signal-brand span {{
        display: inline-flex; align-items: center; justify-content: center;
        width: 31px; height: 31px; border-radius: 50%;
        color: #000; background: {GREEN}; font-size: 17px;
    }}
    .eyebrow {{
        color: {MUTED}; background: transparent;
        padding: 0;
        text-transform: uppercase; letter-spacing: .1em;
        font-weight: 700; font-size: .68rem; margin: 0 0 .15rem;
    }}
    .hero-copy {{
        color: {MUTED}; font-size: .98rem; line-height: 1.55;
        max-width: 760px; margin: -.25rem 0 .5rem;
    }}
    .insight-box {{
        background: {PANEL}; border: 1px solid #292929; border-radius: 8px;
        padding: 17px 18px; margin: 0 0 .65rem;
        transition: background .2s ease, transform .2s ease;
    }}
    .insight-box:hover {{ background: #242424; transform: translateY(-2px); }}
    .insight-box b::before {{ content: "●"; color: {GREEN}; margin-right: 8px; }}
    .method-box {{
        background: {PANEL}; border: 1px solid #292929; border-radius: 8px;
        padding: 18px 20px; color: {MUTED}; font-size: .88rem;
    }}
    div[data-baseweb="select"] > div, .stDateInput input {{
        background-color: #181818 !important; border-color: #3E3E3E !important;
        border-radius: 6px !important;
    }}
    .stButton > button, .stDownloadButton > button {{
        background: {GREEN}; color: #061209; border: 0; border-radius: 999px;
        font-weight: 800; padding: .62rem 1.3rem;
        transition: transform .15s ease, background .15s ease;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover {{
        background: #3BE477; color: #000; transform: scale(1.03);
    }}
    button[data-baseweb="tab"] {{
        border-radius: 4px;
        background: transparent;
        padding: 8px 12px;
        margin-right: 4px;
        font-weight: 700;
    }}
    button[data-baseweb="tab"][aria-selected="true"] {{ background: #282828; color: {TEXT}; }}
    [data-testid="stExpander"] {{ background: {PANEL}; border: 1px solid #292929; border-radius: 8px; }}
    hr {{ border-color: #292929; }}
    .app-footer {{
        display: flex; align-items: center; justify-content: space-between; gap: 24px;
        margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #242424;
        color: #8D8D8D; font-size: .76rem; line-height: 1.45;
    }}
    .app-footer strong {{ color: #C8C8C8; font-weight: 700; }}
    .app-footer-meta {{ text-align: right; white-space: nowrap; }}
    @media (max-width: 1000px) {{
        .block-container {{ padding-top: 1.25rem; padding-bottom: 1.25rem; }}
        h1 {{ font-size: 2rem !important; }}
        [data-testid="stHorizontalBlock"] {{
            flex-direction: column !important;
            gap: .85rem !important;
        }}
        [data-testid="column"] {{
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }}
        [data-testid="stMetric"] {{ min-height: 96px; }}
        .app-footer {{ display: block; }}
        .app-footer-meta {{ text-align: left; white-space: normal; margin-top: 6px; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


def plot_layout(fig: go.Figure, height: int = 410) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font={"family": "DM Sans", "color": TEXT, "size": 13},
        margin={"l": 35, "r": 25, "t": 55, "b": 35},
        legend_title_text="",
        hoverlabel={"bgcolor": "#282828", "font_color": TEXT, "bordercolor": "#404040"},
        coloraxis_colorbar={"outlinewidth": 0, "tickcolor": MUTED},
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor="#404040", tickfont_color=MUTED)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor="#404040", tickfont_color=MUTED)
    return fig


@st.cache_resource
def initialize() -> str:
    return str(ensure_database())


@st.cache_data
def get_data():
    return load_daily(), load_creators(), load_content_performance()


@st.cache_data
def get_experiment():
    return experiment_summary()


initialize()
daily, creators, content_perf = get_data()

st.sidebar.markdown('<div class="signal-brand"><span>≋</span> SIGNAL</div>', unsafe_allow_html=True)
page = st.sidebar.radio(
    "Navigate",
    ["Executive Overview", "Opportunity Explorer", "Experiment Measurement", "AI Strategy Brief"],
    label_visibility="collapsed",
)
st.sidebar.divider()
st.sidebar.markdown("#### Global filters")
st.sidebar.caption("Leave a filter blank to include all values.")
all_markets = sorted(daily.market.unique())
all_categories = sorted(daily.category.unique())
all_formats = sorted(daily.format.unique())
markets = st.sidebar.multiselect("Markets", all_markets, default=[], placeholder="All markets", key="markets_v2")
categories = st.sidebar.multiselect(
    "Categories", all_categories, default=[], placeholder="All categories", key="categories_v2"
)
formats = st.sidebar.multiselect("Formats", all_formats, default=[], placeholder="All formats", key="formats_v2")
min_date, max_date = pd.to_datetime(daily.date).min().date(), pd.to_datetime(daily.date).max().date()
date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]

filtered = filter_daily(
    daily,
    markets or all_markets,
    categories or all_categories,
    formats or all_formats,
    start_date,
    end_date,
)
kpis = headline_kpis(filtered)
opportunities = category_opportunities(filtered)
experiment_metrics, balance, segments = get_experiment()

st.markdown('<div class="eyebrow">Podcast & Video Analytics</div>', unsafe_allow_html=True)

if page == "Executive Overview":
    st.title("Where should content investment go next?")
    st.markdown(
        '<div class="hero-copy">A decision-oriented view of audience behavior, content momentum, and '
        "incremental impact across podcast and video formats.</div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    cols[0].metric("Active audience", f"{kpis['active_audience']/1e6:.2f}M")
    cols[1].metric("Engagement hours", f"{kpis['engagement_hours']/1e6:.2f}M")
    cols[2].metric("Completion rate", f"{kpis['completion_rate']:.1%}")
    cols[3].metric("Video adoption", f"{kpis['video_adoption']:.1%}")

    left, right = st.columns([1.7, 1])
    with left:
        st.subheader("Category opportunity map")
        if not opportunities.empty:
            fig = px.scatter(
                opportunities,
                x="starts_growth",
                y="hours_per_1k_audience",
                size="audience_share",
                color="opportunity_score",
                text="category",
                color_continuous_scale=[[0, "#3A433D"], [1, GREEN]],
                labels={
                    "starts_growth": "Start growth",
                    "hours_per_1k_audience": "Engagement hours / 1K audience",
                    "opportunity_score": "Opportunity",
                },
            )
            fig.update_traces(textposition="top center", marker={"line": {"width": 1, "color": "#829087"}})
            fig.update_xaxes(tickformat=".0%")
            st.plotly_chart(plot_layout(fig, 455), use_container_width=True)
    with right:
        st.subheader("Priority investments")
        for idx, row in opportunities.head(3).reset_index(drop=True).iterrows():
            st.markdown(
                f'<div class="insight-box"><b>{idx + 1}. {row.category}</b><br>'
                f'<span style="color:{MUTED}">Score {row.opportunity_score:.0f}/100 · '
                f"Growth {row.starts_growth:.1%} · Completion {row.completion_rate:.1%}</span></div>",
                unsafe_allow_html=True,
            )
        st.caption("Opportunity score combines growth, engagement intensity, and audience scale.")

    st.subheader("Consumption momentum by format")
    trend = filtered.groupby(["date", "format"], as_index=False).consumed_minutes.sum()
    trend["engagement_hours"] = trend.consumed_minutes / 60
    fig = px.line(
        trend,
        x="date",
        y="engagement_hours",
        color="format",
        color_discrete_map={"Video": GREEN, "Audio": "#8D98A1"},
        labels={"engagement_hours": "Engagement hours", "date": ""},
    )
    st.plotly_chart(plot_layout(fig, 350), use_container_width=True)

elif page == "Opportunity Explorer":
    st.title("Find the next content growth pocket")
    st.markdown(
        '<div class="hero-copy">Compare category momentum, market demand, video adoption, episode length, '
        "and creator health using the global filters.</div>",
        unsafe_allow_html=True,
    )
    tab1, tab2, tab3 = st.tabs(["Category & market", "Format & duration", "Creator health"])
    with tab1:
        market = (
            filtered.groupby(["market", "category"], as_index=False)
            .agg(starts=("starts", "sum"), completions=("completions", "sum"), minutes=("consumed_minutes", "sum"))
        )
        market["completion_rate"] = market.completions / market.starts
        fig = px.treemap(
            market,
            path=["market", "category"],
            values="starts",
            color="completion_rate",
            color_continuous_scale=[[0, "#303632"], [1, GREEN]],
            labels={"completion_rate": "Completion"},
        )
        st.plotly_chart(plot_layout(fig, 520), use_container_width=True)
        st.dataframe(
            opportunities[["category", "starts_growth", "completion_rate", "hours_per_1k_audience", "opportunity_score"]]
            .style.format(
                {"starts_growth": "{:.1%}", "completion_rate": "{:.1%}", "hours_per_1k_audience": "{:,.1f}", "opportunity_score": "{:.0f}"}
            ),
            use_container_width=True,
            hide_index=True,
        )
    with tab2:
        perf = content_perf[
            content_perf.market.isin(markets or all_markets)
            & content_perf.category.isin(categories or all_categories)
            & content_perf.format.isin(formats or all_formats)
        ].copy()
        perf["duration_band"] = pd.cut(
            perf.duration_minutes, bins=[0, 25, 45, 65, 200], labels=["Under 25m", "25–45m", "45–65m", "65m+"]
        )
        duration = perf.groupby(["duration_band", "format"], observed=True, as_index=False).agg(
            starts=("starts", "sum"), completions=("completions", "sum")
        )
        duration["completion_rate"] = duration.completions / duration.starts
        fig = px.bar(
            duration,
            x="duration_band",
            y="completion_rate",
            color="format",
            barmode="group",
            color_discrete_map={"Video": GREEN, "Audio": "#8D98A1"},
            labels={"duration_band": "Episode length", "completion_rate": "Completion rate"},
        )
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(plot_layout(fig, 460), use_container_width=True)
    with tab3:
        c = creators[creators.primary_category.isin(categories or all_categories)].copy()
        fig = px.scatter(
            c,
            x="monthly_release_cadence",
            y="audience_growth_rate",
            size="audience_size",
            color="creator_retention_rate",
            hover_name="creator_name",
            color_continuous_scale=[[0, "#39403B"], [1, GREEN]],
            labels={
                "monthly_release_cadence": "Monthly release cadence",
                "audience_growth_rate": "Audience growth",
                "creator_retention_rate": "Creator retention",
            },
        )
        fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(plot_layout(fig, 480), use_container_width=True)
        st.dataframe(
            c[["creator_name", "primary_category", "monthly_release_cadence", "audience_growth_rate", "creator_retention_rate"]]
            .head(15)
            .style.format({"audience_growth_rate": "{:.1%}", "creator_retention_rate": "{:.1%}"}),
            use_container_width=True,
            hide_index=True,
        )

elif page == "Experiment Measurement":
    discovery = experiment_metrics.iloc[0]
    ship = discovery.ci_low > 0
    st.title("Do promoted video clips drive discovery?")
    st.markdown(
        '<div class="hero-copy">Randomized measurement of whether short-form video promotion increases '
        "full-episode discovery without reducing listening depth.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="insight-box"><b>{"Ship with a measured rollout" if ship else "Do not ship broadly"}</b><br>'
        f'<span style="color:{MUTED}">Primary metric lift: {discovery.relative_lift:.1%} relative · '
        f"95% CI {discovery.ci_low:.1%} to {discovery.ci_high:.1%} absolute</span></div>",
        unsafe_allow_html=True,
    )
    cols = st.columns(4)
    cols[0].metric("Control users", f"{balance['control_n']:,}")
    cols[1].metric("Treatment users", f"{balance['treatment_n']:,}")
    cols[2].metric("Required / group", f"{balance['required_per_group']:,}")
    cols[3].metric("Pre-period delta", f"{balance['pre_minutes_delta']:+.2f} min")

    outcome_cols = st.columns(3)
    for column, (_, outcome) in zip(outcome_cols, experiment_metrics.iterrows()):
        is_rate = "rate" in outcome.metric.lower()
        value = f"{outcome.treatment:.1%}" if is_rate else f"{outcome.treatment:.1f} min"
        delta = f"{outcome.absolute_lift:+.1%} absolute" if is_rate else f"{outcome.absolute_lift:+.1f} min"
        column.metric(outcome.metric, value, delta)

    rate_chart = experiment_metrics.iloc[:2].copy()
    fig = go.Figure()
    fig.add_bar(name="Control", x=rate_chart.metric, y=rate_chart.control, marker_color="#7D8881")
    fig.add_bar(
        name="Treatment",
        x=rate_chart.metric,
        y=rate_chart.treatment,
        marker_color=GREEN,
    )
    fig.update_layout(barmode="group", title="Treatment vs. control rate outcomes")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(plot_layout(fig, 430), use_container_width=True)
    st.subheader("Market-level discovery effects")
    segment_chart = segments.copy()
    segment_chart["error_low"] = segment_chart.absolute_lift - segment_chart.ci_low
    segment_chart["error_high"] = segment_chart.ci_high - segment_chart.absolute_lift
    seg_fig = px.bar(
        segment_chart,
        x="market",
        y="absolute_lift",
        color="absolute_lift",
        color_continuous_scale=[[0, "#3A433D"], [1, GREEN]],
        labels={"absolute_lift": "Absolute lift", "market": "Market"},
    )
    seg_fig.update_traces(
        error_y={
            "type": "data",
            "symmetric": False,
            "array": segment_chart.error_high,
            "arrayminus": segment_chart.error_low,
            "color": "#C7CEC9",
        }
    )
    seg_fig.add_hline(y=0, line_dash="dash", line_color="#7D8881")
    seg_fig.update_yaxes(tickformat=".1%")
    st.plotly_chart(plot_layout(seg_fig, 340), use_container_width=True)
    st.markdown(
        '<div class="method-box"><b>Measurement framework.</b> Primary: full-episode discovery. '
        "Secondary: completion. Guardrail: listening minutes per active user. "
        "Two-sided 95% confidence intervals; 80% power for a 2-point minimum detectable effect. "
        "Assignment and outcomes are synthetic and reproducible.</div>",
        unsafe_allow_html=True,
    )

else:
    st.title("Turn metrics into a decision brief")
    st.markdown(
        '<div class="hero-copy">A grounded synthesis workflow that uses only computed dashboard metrics, '
        "preserves metric citations, and explicitly communicates limitations.</div>",
        unsafe_allow_html=True,
    )
    brief = generate_strategy_brief(opportunities, experiment_metrics, kpis)
    evidence = build_evidence_register(opportunities, experiment_metrics, kpis)
    st.markdown(brief)
    download_cols = st.columns(2)
    download_cols[0].download_button(
        "Download strategy brief",
        brief,
        file_name="spotify_content_strategy_brief.md",
        mime="text/markdown",
    )
    download_cols[1].download_button(
        "Download evidence register",
        evidence.to_csv(index=False),
        file_name="spotify_strategy_evidence.csv",
        mime="text/csv",
    )
    st.divider()
    st.subheader("Grounding contract")
    st.markdown(
        '<div class="method-box">Every quantitative claim above is formatted directly from the filtered KPI '
        "frames or experiment output. No external facts or unsupported causal claims are inserted. "
        "This deterministic layer can be passed to an LLM for tone and narrative refinement without allowing "
        "the model to create new metrics.</div>",
        unsafe_allow_html=True,
    )
    with st.expander("View claim-to-metric evidence register"):
        st.dataframe(evidence[["evidence_id", "metric", "display_value", "source"]], use_container_width=True, hide_index=True)

st.markdown(
    '<footer class="app-footer">'
    '<div><strong>Signal</strong> · Podcast & Video Analytics Intelligence Platform</div>'
    '<div class="app-footer-meta">Synthetic behavioral data · Public metadata enrichment optional · Independent portfolio project</div>'
    "</footer>",
    unsafe_allow_html=True,
)
