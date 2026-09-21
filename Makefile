.PHONY: ci
ci:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src tests
	uv run pytest -q -m "not local_model"
	for check in checks/*.sh; do \
		if [ -x "$$check" ]; then \
			"$$check" || exit $$?; \
		fi \
	done

.PHONY: doctor
doctor:
	python -m clinicloop.setup.doctor

.PHONY: setup
setup:
	python -m clinicloop.setup.install

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  ci       - Run linting, type checking, and tests"
	@echo "  doctor   - Check system configuration"
	@echo "  setup    - Install dependencies and setup"
