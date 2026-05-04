.PHONY: install setup-index chat teardown

install:
	pip install -r requirements.txt

setup-index:
	python opensearch/index_setup.py

chat:
	python chat.py

teardown:
	python opensearch/teardown.py
