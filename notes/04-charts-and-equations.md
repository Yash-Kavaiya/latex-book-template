# Charts and equations

This chapter exercises a larger, multi-branch diagram, a Mermaid chart, and
typeset mathematics. Every figure here is automatically scaled to at most
the text width and 85% of the page height (see [Images](02-layout-and-diagrams.md#images)),
so a wide or tall diagram never overflows the margins -- the source only
declares an *intended* size, and the layout stays responsive to it.

## A larger diagram

```mermaid {#fig:architecture caption="Request path through the build pipeline" align=center width=92%}
flowchart TB
  subgraph Author machine
    A[notes/*.md] --> B[book.yml]
  end
  subgraph GitHub Actions
    B --> C[Validate]
    A --> C
    C --> D[Prepare content]
    D --> E[Pandoc]
    E --> F[XeLaTeX]
  end
  F --> G[(book.pdf)]
  F --> H[(latex-source.zip)]
```

## A chart

```mermaid {#fig:effort caption="Relative effort by build stage" align=center width=80%}
pie showData
    "Validation" : 10
    "Content preparation" : 25
    "Pandoc and LaTeX" : 55
    "Packaging" : 10
```

## Equations

Inline math sits naturally in a sentence: the golden ratio is
$\varphi = \dfrac{1 + \sqrt{5}}{2} \approx 1.618$, and Euler's identity is
$e^{i\pi} + 1 = 0$.

A single displayed equation:

$$
E = mc^2
$$

A short derivation uses the `aligned` environment:

$$
\begin{aligned}
  (a + b)^2 &= a^2 + 2ab + b^2 \\
            &= a^2 + b^2 + 2ab
\end{aligned}
$$

Piecewise definitions use `cases`:

$$
f(n) =
\begin{cases}
  1 & n = 0 \\
  n \cdot f(n - 1) & n > 0
\end{cases}
$$

Return to the [welcome](01-welcome.md#welcome) chapter, or review the
[component inventory](03-reference-tables.md#component-inventory).
