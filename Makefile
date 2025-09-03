.PHONY: run lint format test mypy
run:
	python -m python_homework_03.api

test:
	pytest tests

lint:
	ruff check python_homework_03

format:
	ruff format python_homework_03

mypy:
	mypy python_homework_03