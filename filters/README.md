# Maintainer filters

Pandoc Lua filters, applied only when writing LaTeX (`FORMAT == "latex"`).

* `longtable.lua` — normalizes explicit table column widths, tightens
  padding/font size once a table reaches six or more columns, and turns a
  `{.landscape}` fenced div into a rotated `landscape` environment.

Image and Mermaid handling happens before Pandoc runs, in
`scripts/prepare-content.py`, because it needs to render diagrams and copy
assets — not just transform the AST.
