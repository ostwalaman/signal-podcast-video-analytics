# Data Sources, Assumptions, and Limitations

## Default Demonstration Data

The application uses deterministic synthetic data generated with seed `20260609`.

Synthetic fields include:

- All creator and content records in the default catalog
- All impressions, starts, completions, consumed minutes, audience, and repeat-consumption events
- All treatment assignments and experiment outcomes
- Creator audience, retention, and growth measures

The data intentionally contains directional patterns that make it possible to demonstrate trend detection, opportunity prioritization, experiment analysis, and stakeholder storytelling. It must not be interpreted as Spotify performance.

## Optional Public Metadata

`src.data_pipeline.fetch_public_podcast_metadata()` can fetch public podcast catalog metadata from the Apple Search API. The returned fields are show name, creator, public genre, country, feed URL, and Apple collection identifier.

The default dashboard does not call the API, so setup and tests remain reproducible without network access. Public metadata can be used to replace or enrich the catalog layer while retaining synthetic behavioral events.

## Key Assumptions

- Starts are used as a consumption-intent measure.
- Completion means the user reached the modeled completion threshold.
- Repeat consumption counts active audience members returning within the aggregation period.
- Opportunity score weights growth at 40%, engagement intensity at 40%, and audience share at 20%.
- The experiment is randomized, balanced, and modeled to test promoted video clips.

## Limitations

- Synthetic events do not reproduce all real-world selection effects, seasonality, or platform dynamics.
- Aggregate content metrics cannot replace user-level retention or long-term value analysis.
- Opportunity scores are directional prioritization aids, not causal investment estimates.
- Experiment segment cuts are exploratory and should be corrected for multiple comparisons in production.
- Production decisions require stakeholder context, data-quality review, and operational constraints.

