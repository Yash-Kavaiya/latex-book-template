.PHONY: all validate clean

all: build/book.pdf

validate:
	python3 scripts/build.py --validate-only

build/book.pdf: book.yml config/book.schema.json templates/book.tex scripts/build.py $(shell find chapters -type f -name '*.md')
	python3 scripts/build.py --output $@

clean:
	rm -rf build
