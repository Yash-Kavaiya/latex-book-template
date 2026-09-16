#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python scripts/validate.py
command -v pandoc >/dev/null || { echo "pandoc is required" >&2; exit 1; }
command -v latexmk >/dev/null || { echo "latexmk is required" >&2; exit 1; }
test -x node_modules/.bin/mmdc || { echo "run npm install first" >&2; exit 1; }

rm -rf build/book-latex-source dist
mkdir -p build/book-latex-source dist
python scripts/render_mermaid.py
cp -R notes/assets build/book-latex-source/assets
mkdir -p build/book-latex-source/build
cp -R build/mermaid build/book-latex-source/build/mermaid

pandoc build/book.md \
  --from=markdown-raw_html-raw_tex \
  --to=latex --standalone --toc \
  --metadata-file=book.yml \
  --include-in-header=templates/preamble.tex \
  --resource-path=.:notes \
  --output=build/book-latex-source/main.tex

(
  cd build/book-latex-source
  SOURCE_DATE_EPOCH=0 latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
)
cp build/book-latex-source/main.pdf dist/book.pdf
find build/book-latex-source -maxdepth 1 -type f ! -name main.tex -delete
tar --sort=name --mtime='@0' --owner=0 --group=0 --numeric-owner \
  -czf dist/book-latex-source.tar.gz -C build book-latex-source
echo "Built dist/book.pdf and dist/book-latex-source.tar.gz"
