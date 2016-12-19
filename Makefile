.PHONY: all test clean

test:
	pip install -r requirements.txt
	pytest

code-convention:
	pip install -r requirements.txt
	flake8
	pycodestyle