.PHONY: venv install fmt lint type test all run clean

venv:
	python3.11 -m venv .venv || python3 -m venv .venv

install:
	. .venv/bin/activate && pip install -U pip && pip install -e . && pip install pytest pytest-cov black isort ruff mypy

fmt:
	. .venv/bin/activate && black src tests && isort src tests

lint:
	. .venv/bin/activate && ruff check src tests

type:
	. .venv/bin/activate && mypy src

test:
	. .venv/bin/activate && pytest

all: fmt lint type test

run:
	. .venv/bin/activate && python -m gptrader.cli --help

clean:
	rm -rf .venv .pytest_cache .mypy_cache .ruff_cache artifacts/*.tmp
