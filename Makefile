.PHONY: all validate build test clean

all: build

validate:
	python3 scripts/validate.py
	python3 scripts/build.py --validate-only

build:
	bash scripts/build-book.sh

test:
	python3 -m unittest discover -s tests -v

clean:
	rm -rf build dist node_modules
