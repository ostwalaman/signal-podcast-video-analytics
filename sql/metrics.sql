-- Reproducible KPI layer. All behavioral data is synthetic and disclosed.

CREATE OR REPLACE VIEW content_performance AS
SELECT
    e.content_id,
    c.creator_id,
    c.title,
    e.category,
    e.market,
    e.format,
    c.duration_minutes,
    SUM(e.impressions) AS impressions,
    SUM(e.starts) AS starts,
    SUM(e.completions) AS completions,
    SUM(e.active_audience) AS active_audience,
    SUM(e.repeat_consumers) AS repeat_consumers,
    SUM(e.consumed_minutes) AS consumed_minutes,
    SUM(e.starts)::DOUBLE / NULLIF(SUM(e.impressions), 0) AS start_rate,
    SUM(e.completions)::DOUBLE / NULLIF(SUM(e.starts), 0) AS completion_rate,
    SUM(e.repeat_consumers)::DOUBLE / NULLIF(SUM(e.active_audience), 0) AS repeat_rate
FROM engagement e
JOIN content c USING (content_id)
GROUP BY ALL;

CREATE OR REPLACE VIEW daily_kpis AS
SELECT
    date,
    market,
    category,
    format,
    SUM(impressions) AS impressions,
    SUM(starts) AS starts,
    SUM(completions) AS completions,
    SUM(active_audience) AS active_audience,
    SUM(repeat_consumers) AS repeat_consumers,
    SUM(consumed_minutes) AS consumed_minutes,
    SUM(completions)::DOUBLE / NULLIF(SUM(starts), 0) AS completion_rate,
    SUM(repeat_consumers)::DOUBLE / NULLIF(SUM(active_audience), 0) AS repeat_rate
FROM engagement
GROUP BY ALL;

CREATE OR REPLACE VIEW creator_performance AS
SELECT
    cr.creator_id,
    cr.creator_name,
    cr.primary_category,
    cr.monthly_release_cadence,
    cr.audience_size,
    cr.creator_retention_rate,
    cr.audience_growth_rate,
    SUM(e.consumed_minutes) AS consumed_minutes,
    SUM(e.completions)::DOUBLE / NULLIF(SUM(e.starts), 0) AS completion_rate
FROM creators cr
JOIN content c USING (creator_id)
JOIN engagement e USING (content_id)
GROUP BY ALL;

