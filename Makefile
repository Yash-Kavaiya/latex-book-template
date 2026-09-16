.PHONY: all validate clean

all: build/book.pdf

validate:
	python3 scripts/build.py --validate-only

build/book.pdf: book.yml config/book.schema.json templates/book.tex scripts/build.py $(shell find chapters -type f -name '*.md')
	python3 scripts/build.py --output $@

clean:
	rm -rf build
PANDOC ?= pandoc
LATEX ?= xelatex
CONTENT := $(shell find content -name '*.md' -type f | sort)

.PHONY: all clean test
all: build/book.pdf

node_modules/.bin/mmdc: package.json
	npm install --no-save

build/prepared.md: $(CONTENT) scripts/prepare-content.py node_modules/.bin/mmdc
	python3 scripts/prepare-content.py --assets-dir build/assets -o $@ $(CONTENT)

build/book.tex: build/prepared.md filters/longtable.lua templates/book.tex
	$(PANDOC) --standalone --from markdown+fenced_divs+link_attributes --to latex \
		--lua-filter filters/longtable.lua --template templates/book.tex -o $@ $<

build/book.pdf: build/book.tex
	$(LATEX) -output-directory=build -interaction=nonstopmode -halt-on-error build/book.tex
	$(LATEX) -output-directory=build -interaction=nonstopmode -halt-on-error build/book.tex

test:
	python3 -m unittest discover -s tests -v

clean:
	rm -rf build node_modules
