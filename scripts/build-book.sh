#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
BUILD="$ROOT/build"

die() { printf 'error: %s\n' "$*" >&2; exit 1; }
for command in python3 pandoc latexmk xelatex mmdc; do
  command -v "$command" >/dev/null 2>&1 || die "required command '$command' was not found; use the provided Dockerfile"
done

rm -rf -- "$BUILD"
mkdir -p -- "$BUILD"

python3 "$ROOT/scripts/preprocess.py" "$ROOT/book.yaml" "$BUILD"
mapfile -t chapters < "$BUILD/chapter-list.txt"
((${#chapters[@]})) || die "preprocessing produced an empty chapter list"

if ! pandoc "${chapters[@]}" \
  --from=markdown --standalone --top-level-division=chapter \
  --metadata-file="$ROOT/book.yaml" \
  --template="$ROOT/templates/book.tex" \
  --pdf-engine=xelatex \
  --output="$BUILD/book.tex"; then
  die "Pandoc failed; check Markdown syntax and referenced assets"
fi

if ! latexmk -xelatex -interaction=nonstopmode -halt-on-error \
  -output-directory="$BUILD" "$BUILD/book.tex"; then
  die "LaTeX compilation failed; inspect $BUILD/book.log for the exact error"
fi
[[ -s "$BUILD/book.pdf" ]] || die "LaTeX completed without producing build/book.pdf"
printf 'Built %s\n' "$BUILD/book.pdf"

