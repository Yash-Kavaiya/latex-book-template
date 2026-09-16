# LaTeX book template

Write all book content in `notes/`. The `chapters` array in `book.yaml` is the
authoritative chapter order; paths are **not** discovered automatically. Numeric
filename prefixes such as `01-introduction.md`, `02-methods.md` are recommended
so directory listings also appear in reading order.

## Build

With Pandoc, XeLaTeX, latexmk, Python/PyYAML, and Mermaid CLI installed:

```sh
./scripts/build-book.sh
```

The clean, isolated `build/` directory contains `book.tex`, `book.pdf`, LaTeX
logs, prepared Markdown, and rendered diagrams. It is safe to delete and is not
versioned. The script validates the YAML and all chapter and image paths before
running Pandoc once, then uses `latexmk` to resolve the required LaTeX passes.

For the pinned toolchain, use Docker:

```sh
docker build -t latex-book .
docker run --rm -v "$PWD/build:/book/build" latex-book
```

Mermaid fenced code blocks are rendered automatically:

````markdown
```mermaid
flowchart LR
  Draft --> Book
```
````
