.PHONY: all test clean

init:
	pip install -r requirements.txt

test:
	pytest

code-convention:
	flake8
	pycodestyle
