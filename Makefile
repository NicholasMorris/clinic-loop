# Scaffolder-owned. Later issues add checks as files under checks/, never as edits here.

# Every tool runs through uv with the dev extra so a fresh checkout works. The lockfile is
# honoured as written (--locked). Override RUN to substitute the launcher.
RUN ?= uv run --locked --extra dev --extra docs --extra sim --extra api --extra agents

.PHONY: ci
ci:
	$(RUN) ruff check .
	$(RUN) ruff format --check .
	$(RUN) mypy
	$(RUN) pytest -q -m "not local_model"
	@export LC_ALL=C; \
	for check in checks/*.sh; do \
		[ -x "$$check" ] || continue; \
		echo "checks: $$check"; \
		"$$check" || exit $$?; \
	done

.PHONY: doctor
doctor:
	uv run python -m clinicloop.setup.doctor

.PHONY: setup
setup:
	uv run python -m clinicloop.setup.install

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  ci      - ruff, mypy, pytest, then every executable checks/*.sh in lexical order"
	@echo "  doctor  - check system configuration"
	@echo "  setup   - install dependencies and set up the machine"
