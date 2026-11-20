.PHONY: check-env set-key run test eval live clean

VENV = venv
PYTHON = $(VENV)/Scripts/python
STREAMLIT = $(VENV)/Scripts/streamlit
PYTEST = $(VENV)/Scripts/pytest

check-env:
	$(PYTHON) scripts/check_env.py

set-key:
	$(PYTHON) scripts/set_key.py

run:
	$(STREAMLIT) run app.py

test:
	$(PYTEST) tests/ -v

eval:
	$(PYTHON) evals/run_evals.py

live:
	$(PYTHON) scripts/check_env.py
	$(PYTEST) tests/ -v
	$(PYTHON) evals/run_evals.py --live

clean:
	rm -rf __pycache__ .pytest_cache htmlcov
