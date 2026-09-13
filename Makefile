.PHONY: setup test validate
setup:
	scripts/setup/setup-python.sh
test:
	.venv/bin/python -m pytest -q cli/tests
validate:
	.venv/bin/python -c "from devcli.config import validate_all_registries as v; print('registries valid:', v())"
