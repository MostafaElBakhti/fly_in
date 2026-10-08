.PHONY: install run debug clean lint lint-strict

intall:
	python3 -m pip install pygame flake8 mypy

run:
	PYGAME_HIDE_SUPPORT_PROMPT=1 python3 main.py

debug:
	python3 -m pdb main.py

clean:
	rm -rf __pycache__ .mypy_cache

lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores \
	--ignore-missing-imports --disallow-untyped-defs \
	--check-untyped-defs

lint-strict:
	flake8 .
	mypy . --strict