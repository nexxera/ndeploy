.PHONY: test all
.DEFAULT_GOAL := test

init:
	pip install -r requirements.txt

test:
	pytest

code-convention:
	flake8
	pycodestyle

clean:
	rm -rf dist ndeploy.egg-info build reports

release: clean
	python setup.py sdist bdist_wheel

upload: release
	twine upload dist/*

all : init code-convention clean release
