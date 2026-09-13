.PHONY: setup run test
VENV=.venv
PY=$(VENV)/bin/python

setup:
	python3 -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -e ".[dev]"

run:
	FLASK_APP=app FLASK_ENV=development $(VENV)/bin/flask run --port $${PORT:-5000}

test:
	$(PY) -m pytest -q
