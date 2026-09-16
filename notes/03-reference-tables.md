# Reference tables

## Component inventory

The following deliberately long table demonstrates a table that can flow over
more than one page in the PDF.

| Number | Component | Responsibility |
|---:|---|---|
| 01 | Chapter source | Stores semantic prose and headings. |
| 02 | Configuration | Declares metadata and chapter order. |
| 03 | Validator | Checks configuration before expensive work. |
| 04 | Asset scanner | Detects missing and unused files. |
| 05 | Link scanner | Resolves chapter paths and heading fragments. |
| 06 | Reference scanner | Matches reference-style links. |
| 07 | Footnote scanner | Matches footnote uses and definitions. |
| 08 | Label scanner | Enforces globally unique figures. |
| 09 | Mermaid extractor | Writes diagram source files. |
| 10 | Mermaid CLI | Converts diagrams to SVG. |
| 11 | Pandoc reader | Parses restricted Markdown. |
| 12 | Pandoc AST | Represents the combined book. |
| 13 | LaTeX writer | Emits portable TeX source. |
| 14 | XeLaTeX | Selects modern OpenType fonts. |
| 15 | Longtable | Breaks tall tables over pages. |
| 16 | Hyperref | Creates navigable PDF links. |
| 17 | Latexmk | Repeats TeX until references settle. |
| 18 | PDF output | Provides the reader-facing book. |
| 19 | Source archive | Provides independently compilable TeX. |
| 20 | Validation job | Gives quick pull-request feedback. |
| 21 | Build job | Runs only after validation passes. |
| 22 | Artifact upload | Publishes successful main-branch output. |
| 23 | Package manifest | Pins the Mermaid renderer version. |
| 24 | Requirements | Pins Python validation libraries. |
| 25 | JSON Schema | Rejects misspelled configuration fields. |
| 26 | TeX template | Centralizes typesetting policy. |
| 27 | Build directory | Contains disposable intermediates. |
| 28 | Distribution directory | Contains deliverable artifacts. |
| 29 | Static SVG | Illustrates source-controlled artwork. |
| 30 | Generated SVG | Illustrates reproducible diagrams. |
| 31 | CI cache | Speeds dependency installation. |
| 32 | Chapter heading | Defines a PDF chapter. |
| 33 | Section heading | Defines navigation within a chapter. |
| 34 | Code fence | Preserves syntax and spacing. |
| 35 | Caption | Describes a table or figure. |
| 36 | Identifier | Provides a stable cross-reference target. |
| 37 | Relative link | Connects chapters in source form. |
| 38 | Metadata | Populates the title page and PDF properties. |
| 39 | Font setting | Selects serif, sans, and monospace faces. |
| 40 | Reproduction command | Rebuilds the downloaded source archive. |

: Build components and responsibilities. {#tbl:components}

Return to the [welcome](01-welcome.md#welcome) or review the
[build diagram](02-layout-and-diagrams.md#diagrams).
