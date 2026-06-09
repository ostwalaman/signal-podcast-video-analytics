.PHONY: data test run

data:
	python3 -m src.data_pipeline

test:
	python3 -m pytest -q

run:
	streamlit run app.py

