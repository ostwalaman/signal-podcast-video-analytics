# Deployment Guide

The dashboard runs without API keys or external databases. Its DuckDB database is generated automatically on first launch.

## Streamlit Community Cloud

1. Push the repository to GitHub.
2. Create a Streamlit Community Cloud application.
3. Select `app.py` as the entry point.
4. Deploy without adding secrets.

The platform installs dependencies from `requirements.txt`. The generated DuckDB file is excluded from Git and rebuilt from the deterministic pipeline.

## Local Production Check

```bash
python3 -m pytest -q
python3 -m src.data_pipeline
streamlit run app.py --server.headless true
```

## Deployment Verification

- Confirm all four navigation pages load.
- Confirm blank filters include all values.
- Confirm the experiment recommendation and confidence intervals render.
- Confirm the strategy brief and evidence register download successfully.
- Confirm the synthetic-data disclosure is visible.

