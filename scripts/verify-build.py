#!/usr/bin/env python3
"""Fail CI if the generated TeX/PDF omitted or reordered fixture content."""
import subprocess
from pathlib import Path

tex = Path("build/book.tex").read_text(encoding="utf-8")
needles = ["Nested image caption", "fig:nested", "First Mermaid flow", "Second Mermaid flow",
           "Multiline table caption", "Wide table caption", "Landscape content"]
positions = [tex.index(item) for item in needles]
if positions != sorted(positions):
    raise SystemExit("fixture ordering in book.tex is incorrect")
for required in ("keepaspectratio", r"height=0.85\textheight", "longtable"):
    if required not in tex:
        raise SystemExit(f"book.tex lacks {required}")

pdf_text = subprocess.run(
    ["pdftotext", "build/book.pdf", "-"], check=True, text=True, capture_output=True
).stdout
for item in ("Nested image caption", "First Mermaid flow", "Second Mermaid flow",
             "Multiline table caption", "Wide table caption", "Landscape content"):
    if item not in pdf_text:
        raise SystemExit(f"book.pdf lacks {item}")
