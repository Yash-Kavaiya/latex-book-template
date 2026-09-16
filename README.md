# LaTeX book template

A safe, configuration-driven Pandoc template for producing a book from Markdown.
All user-facing settings—including chapter order, typography, page layout, cover,
and front matter—live in the documented [`book.yml`](book.yml). The JSON Schema
rejects unknown settings and unsafe raw LaTeX or command-like configuration.

## Setup and use

Install Python dependencies and ensure `pandoc` and `xelatex` are available:

```sh
python3 -m pip install -r requirements.txt
make validate       # fast validation, before Pandoc or TeX starts
make                # writes build/book.pdf
```

Validation reports the property and reason for malformed dimensions, unsupported
paper sizes, invalid colors, and missing or inaccessible chapter/cover files.
Chapter and asset paths are confined to the directory containing `book.yml`.

The build script passes a temporary JSON metadata file to Pandoc and supplies
chapter paths as argument-list elements (never through a shell). Free-form text is
LaTeX-escaped; values used structurally are schema allowlists. Consequently,
configuration cannot add commands, document classes, or raw template fragments.
This template turns one or more Markdown chapters into a book while handling
the parts of Pandoc publishing that commonly become fragile: chapter-relative
images, Mermaid diagrams, wide/page-breaking tables, and safe LaTeX text.

## Build

Install Pandoc, XeLaTeX, Node.js, and `pdftotext`, then run:

```sh
make
python3 scripts/verify-build.py
```

`npm install` installs the exact (non-range) Mermaid CLI version recorded in
`package.json`. The build never invokes a shell with content-derived
arguments. Generated and copied files live only under `build/assets`; copied
asset names include a hash of their canonical source path so equal basenames
from different chapters cannot collide.

## Figures

Paths are relative to each chapter, including paths containing spaces:

```markdown
![A caption](<images/a file.png>){#fig:example width=60% height=8cm align=left}
```

`width`, `height`, `align` (`left`, `center`, or `right`), a caption, and a
label are optional. Figures default to centered and are always rendered with
`keepaspectratio`; default bounds are `\linewidth` by `0.85\textheight`.
Missing files produce an obvious typeset placeholder and warning. Pass
`--strict` directly to `prepare-content.py` when a missing image must fail the
build.

Mermaid fences accept the same presentation attributes; their caption is an
explicit `caption` attribute:

````markdown
```mermaid {#fig:flow caption="Request flow" align=center width=80%}
flowchart LR
  Request --> Response
```
````

## Tables

Pandoc emits LaTeX `longtable` output, including repeated headings, captions,
and labels. The Lua filter normalizes explicit column widths and reduces cell
padding/font size for tables with six or more columns without wrapping the
table in an unbreakable resize box. Put exceptionally wide material in a
`{.landscape}` fenced div.
