# Welcome

This small book demonstrates the authoring contract. Continue with the
[layout chapter](02-layout-and-diagrams.md#diagrams), or jump to the
[inventory](03-reference-tables.md#component-inventory).

## Ordinary Markdown

Text may be *emphasized* or **strong**. Lists and links work as expected:

1. Write a chapter.
2. Add it to `book.yml`.
3. Run the [validation command][validation].

> Prefer clear prose over clever formatting.

```python
def greeting(name: str) -> str:
    return f"Hello, {name}!"
```

The same source is useful on the web and on paper.[^portable]

![A set of connected book pages](assets/book-pages.svg){#fig:book-pages width=65%}

[validation]: ../README.md#validate-and-build-locally
[^portable]: Footnotes are collected and typeset by Pandoc.
