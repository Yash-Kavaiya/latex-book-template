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
