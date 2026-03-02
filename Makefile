.PHONY: fmt lint typecheck test check

fmt:
	uv run ruff format yapflame tests

lint:
	uv run ruff check yapflame tests

pyre:
	uv run pyre check

test:
	uv run pytest tests -v

check: fmt lint pyre test
