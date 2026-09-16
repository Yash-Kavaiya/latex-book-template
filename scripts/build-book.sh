#!/usr/bin/env bash
# Single build entry point: notes/**/*.md + book.yml -> build/book.pdf and
# build/book.tex. Used identically by local development, the Dockerfile, and
# .github/workflows/build-book.yml, so behavior never drifts between them.
set -Eeuo pipefail
IFS=$'\n\t'

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
BUILD="$ROOT/build"
cd -- "$ROOT"

die() { printf 'error: %s\n' "$*" >&2; exit 1; }

for command in python3 pandoc latexmk xelatex rsvg-convert; do
  command -v "$command" >/dev/null 2>&1 || die "required command '$command' was not found; use the provided Dockerfile"
done
[[ -x "$ROOT/node_modules/.bin/mmdc" ]] || die "Mermaid CLI is missing; run 'npm ci' first"

rm -rf -- "$BUILD"
mkdir -p -- "$BUILD"

printf '==> Validating notes/ and book.yml\n'
python3 scripts/validate.py

printf '==> Resolving configuration\n'
python3 scripts/build.py \
  --config "$ROOT/book.yml" \
  --metadata-out "$BUILD/metadata.json" \
  --chapters-out "$BUILD/chapters.txt"
mapfile -t chapters < "$BUILD/chapters.txt"
((${#chapters[@]})) || die "no chapters resolved from book.yml"

printf '==> Rendering images and Mermaid diagrams\n'
python3 scripts/prepare-content.py \
  "${chapters[@]}" \
  --assets-dir "$BUILD/assets" \
  --mermaid-command "$ROOT/node_modules/.bin/mmdc" \
  --output "$BUILD/book.md" \
  --strict

printf '==> Rendering LaTeX with Pandoc\n'
if ! pandoc "$BUILD/book.md" \
  --from=markdown+raw_tex \
  --to=latex \
  --standalone \
  --wrap=none \
  --top-level-division=chapter \
  --lua-filter="$ROOT/filters/longtable.lua" \
  --include-in-header="$ROOT/templates/preamble.tex" \
  --metadata-file="$BUILD/metadata.json" \
  --template="$ROOT/templates/book.tex" \
  --output="$BUILD/book.tex"; then
  die "Pandoc failed; check Markdown syntax and referenced assets"
fi

printf '==> Compiling with XeLaTeX (latexmk)\n'
if ! latexmk -xelatex -interaction=nonstopmode -halt-on-error \
  -output-directory="$BUILD" "$BUILD/book.tex"; then
  die "LaTeX compilation failed; inspect $BUILD/book.log for the exact error"
fi

[[ -s "$BUILD/book.pdf" ]] || die "LaTeX completed without producing $BUILD/book.pdf"
[[ -s "$BUILD/book.tex" ]] || die "Pandoc completed without producing $BUILD/book.tex"
printf 'Built %s and %s\n' "$BUILD/book.pdf" "$BUILD/book.tex"
