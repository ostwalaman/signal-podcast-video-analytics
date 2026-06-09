"""Deterministic data pipeline for the analytics portfolio project."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

SEED = 20260609
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "podcast_video.duckdb"
SQL_PATH = ROOT / "sql" / "metrics.sql"

CATEGORIES = [
    "True Crime", "Business", "Technology", "Comedy", "News",
    "Society & Culture", "Health & Fitness", "Education", "Sports", "Kids & Family",
]
MARKETS = ["US", "GB", "DE", "BR", "MX"]
MARKET_SCALE = {"US": 1.00, "GB": 0.56, "DE": 0.47, "BR": 0.64, "MX": 0.52}
CATEGORY_GROWTH = {
    "True Crime": 0.0020, "Business": 0.0017, "Technology": 0.0014,
    "Comedy": 0.0007, "News": 0.0010, "Society & Culture": 0.0009,
    "Health & Fitness": 0.0005, "Education": 0.0006, "Sports": 0.0011,
    "Kids & Family": 0.0003,
}
VIDEO_PROPENSITY = {
    "True Crime": 0.42, "Business": 0.34, "Technology": 0.55, "Comedy": 0.62,
    "News": 0.38, "Society & Culture": 0.44, "Health & Fitness": 0.48,
    "Education": 0.31, "Sports": 0.66, "Kids & Family": 0.28,
}


def fetch_public_podcast_metadata(
    terms: tuple[str, ...] = ("technology", "business", "comedy"),
    limit: int = 25,
) -> pd.DataFrame:
    """Fetch optional public catalog metadata from Apple's Search API.

    The app never depends on this network call. It exists to make it easy to
    enrich the synthetic behavioral layer with attributable public metadata.
    """
    rows: list[dict] = []
    for term in terms:
        query = urllib.parse.urlencode({"term": term, "media": "podcast", "limit": limit})
        with urllib.request.urlopen(
            f"https://itunes.apple.com/search?{query}", timeout=10
        ) as response:
            payload = json.load(response)
        rows.extend(payload.get("results", []))
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    columns = {
        "collectionId": "public_id",
        "collectionName": "show_name",
        "artistName": "creator_name",
        "primaryGenreName": "public_genre",
        "country": "country",
        "feedUrl": "feed_url",
    }
    return frame[list(columns)].rename(columns=columns).drop_duplicates("public_id")


def _creator_name(index: int, category: str) -> str:
    stems = ["Signal", "North", "Open", "Daily", "Deep", "Bright", "Next", "Inside"]
    nouns = ["Room", "Studio", "Brief", "Story", "Angle", "Circuit", "Archive", "Exchange"]
    return f"{stems[index % len(stems)]} {nouns[(index * 3) % len(nouns)]} · {category}"


def generate_creators(rng: np.random.Generator, count: int = 120) -> pd.DataFrame:
    rows = []
    for creator_id in range(1, count + 1):
        category = CATEGORIES[(creator_id - 1) % len(CATEGORIES)]
        audience = int(rng.lognormal(mean=10.2, sigma=0.75))
        cadence = int(rng.choice([1, 2, 4, 8], p=[0.15, 0.35, 0.4, 0.1]))
        rows.append(
            {
                "creator_id": creator_id,
                "creator_name": _creator_name(creator_id, category),
                "primary_category": category,
                "monthly_release_cadence": cadence,
                "audience_size": audience,
                "creator_retention_rate": float(np.clip(rng.normal(0.73, 0.1), 0.42, 0.96)),
                "audience_growth_rate": float(
                    np.clip(rng.normal(CATEGORY_GROWTH[category] * 30, 0.045), -0.12, 0.25)
                ),
            }
        )
    return pd.DataFrame(rows)


def generate_content(rng: np.random.Generator, creators: pd.DataFrame, count: int = 720) -> pd.DataFrame:
    rows = []
    adjectives = ["Hidden", "Future", "Unfiltered", "Essential", "Unexpected", "Modern"]
    topics = ["Signals", "Decisions", "Stories", "Systems", "Breakthroughs", "Questions"]
    start = pd.Timestamp("2025-10-01")
    for content_id in range(1, count + 1):
        creator = creators.iloc[(content_id - 1) % len(creators)]
        category = creator.primary_category
        is_video = rng.random() < VIDEO_PROPENSITY[category]
        duration = int(np.clip(rng.normal(48 if is_video else 39, 18), 8, 120))
        rows.append(
            {
                "content_id": content_id,
                "creator_id": int(creator.creator_id),
                "title": f"{adjectives[content_id % 6]} {topics[(content_id * 5) % 6]} #{content_id}",
                "category": category,
                "format": "Video" if is_video else "Audio",
                "duration_minutes": duration,
                "release_date": start + pd.Timedelta(days=int(rng.integers(0, 230))),
                "market": rng.choice(MARKETS, p=[0.36, 0.16, 0.14, 0.18, 0.16]),
                "metadata_source": "Synthetic catalog modeled on public podcast metadata",
            }
        )
    return pd.DataFrame(rows)


def generate_engagement(
    rng: np.random.Generator, content: pd.DataFrame, days: int = 180
) -> pd.DataFrame:
    dates = pd.date_range("2025-12-01", periods=days, freq="D")
    rows = []
    content_sample = content.sample(n=min(420, len(content)), random_state=SEED).reset_index(drop=True)
    for day_idx, date in enumerate(dates):
        weekend = 0.88 if date.dayofweek >= 5 else 1.0
        for item in content_sample.itertuples(index=False):
            if item.release_date > date:
                continue
            age = max((date - item.release_date).days, 0)
            freshness = 0.54 + 0.46 * np.exp(-age / 55)
            growth = (1 + CATEGORY_GROWTH[item.category]) ** day_idx
            video_boost = 1.18 if item.format == "Video" and item.category in {"Technology", "Sports", "Comedy"} else 1
            lam = 78 * MARKET_SCALE[item.market] * freshness * growth * video_boost * weekend
            impressions = max(int(rng.poisson(lam * 5.5)), 1)
            start_rate = np.clip(rng.normal(0.32 + (0.035 if item.format == "Video" else 0), 0.035), 0.16, 0.52)
            starts = int(rng.binomial(impressions, start_rate))
            duration_effect = -max(item.duration_minutes - 55, 0) * 0.0025
            completion_rate = np.clip(
                rng.normal(0.66 + duration_effect + (0.025 if item.category == "True Crime" else 0), 0.055),
                0.28,
                0.91,
            )
            completions = int(rng.binomial(starts, completion_rate)) if starts else 0
            active_audience = max(int(starts * rng.uniform(0.72, 0.9)), 1)
            repeat_consumers = int(rng.binomial(active_audience, np.clip(0.19 + completion_rate * 0.3, 0, 0.65)))
            consumed_minutes = float(
                starts * item.duration_minutes * np.clip(rng.normal(completion_rate * 0.92, 0.04), 0.2, 0.95)
            )
            rows.append(
                {
                    "date": date,
                    "content_id": item.content_id,
                    "market": item.market,
                    "category": item.category,
                    "format": item.format,
                    "impressions": impressions,
                    "starts": starts,
                    "completions": completions,
                    "active_audience": active_audience,
                    "repeat_consumers": repeat_consumers,
                    "consumed_minutes": round(consumed_minutes, 2),
                }
            )
    return pd.DataFrame(rows)


def generate_experiment(rng: np.random.Generator, count: int = 24000) -> pd.DataFrame:
    """Generate a balanced randomized video-clips promotion experiment."""
    assignment = np.array(["control"] * (count // 2) + ["treatment"] * (count - count // 2))
    rng.shuffle(assignment)
    market = rng.choice(MARKETS, size=count, p=[0.36, 0.16, 0.14, 0.18, 0.16])
    category = rng.choice(CATEGORIES, size=count)
    pre_minutes = np.clip(rng.gamma(shape=3.3, scale=18, size=count), 0, 300)
    baseline_discovery = np.clip(0.13 + pre_minutes / 2200, 0.08, 0.34)
    discovery_lift = np.where(assignment == "treatment", 0.022, 0)
    discovery_lift += np.where((assignment == "treatment") & (category == "Technology"), 0.016, 0)
    discovery_lift += np.where((assignment == "treatment") & (market == "BR"), 0.012, 0)
    discovered = rng.binomial(1, np.clip(baseline_discovery + discovery_lift, 0, 0.8))
    completion_prob = np.clip(0.48 + discovered * 0.18 + np.where(assignment == "treatment", 0.012, 0), 0, 0.9)
    completed = rng.binomial(1, completion_prob)
    post_minutes = np.clip(
        pre_minutes * rng.normal(1.01, 0.18, count)
        + discovered * rng.normal(22, 6, count)
        + np.where(assignment == "treatment", 1.2, 0),
        0,
        420,
    )
    return pd.DataFrame(
        {
            "user_id": np.arange(1, count + 1),
            "assignment": assignment,
            "market": market,
            "preferred_category": category,
            "pre_period_minutes": np.round(pre_minutes, 2),
            "full_episode_discovered": discovered,
            "full_episode_completed": completed,
            "post_period_minutes": np.round(post_minutes, 2),
        }
    )


def build_database(db_path: Path = DB_PATH) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    creators = generate_creators(rng)
    content = generate_content(rng, creators)
    engagement = generate_engagement(rng, content)
    experiment = generate_experiment(rng)
    with duckdb.connect(str(db_path)) as con:
        con.register("creators_df", creators)
        con.register("content_df", content)
        con.register("engagement_df", engagement)
        con.register("experiment_df", experiment)
        con.execute("CREATE OR REPLACE TABLE creators AS SELECT * FROM creators_df")
        con.execute("CREATE OR REPLACE TABLE content AS SELECT * FROM content_df")
        con.execute("CREATE OR REPLACE TABLE engagement AS SELECT * FROM engagement_df")
        con.execute("CREATE OR REPLACE TABLE experiment AS SELECT * FROM experiment_df")
        con.execute(SQL_PATH.read_text())
    return db_path


def ensure_database(db_path: Path = DB_PATH) -> Path:
    if not db_path.exists():
        return build_database(db_path)
    return db_path


if __name__ == "__main__":
    print(f"Built {build_database()}")

