.PHONY: all
.DEFAULT_GOAL := test

init:
	pip install -r requirements.txt

test:
	pytest

code-convention:
	flake8
	pycodestyle

clean:
	rm -rf dist ndeploy.egg-info build

release: clean
	python setup.py sdist bdist_wheel

upload: release
	twine upload dist/*

all : init test code-convention clean release upload
