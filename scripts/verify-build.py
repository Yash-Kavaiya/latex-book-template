#!/usr/bin/env python3
"""Smoke-test a finished build: fail CI if the PDF or TeX is missing content
that the example notes/ chapters are known to produce. Run after
scripts/build-book.sh, from the repository root.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"

TEX_MARKERS = ("keepaspectratio", r"height=0.85\textheight", "longtable", "fancyhdr")
PDF_MARKERS = (
    "Welcome",
    "Layers in the publishing stack",
    "A set of connected book pages",
    "The validated publishing flow",
    "Author and CI review sequence",
    "Component inventory",
    "Chapter source",
    "Stores semantic prose and headings.",
)


def fail(message: str) -> "NoReturn":
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    tex_path = BUILD / "book.tex"
    pdf_path = BUILD / "book.pdf"
    if not tex_path.is_file():
        fail(f"{tex_path} is missing; run scripts/build-book.sh first")
    if not pdf_path.is_file():
        fail(f"{pdf_path} is missing; run scripts/build-book.sh first")

    tex = tex_path.read_text(encoding="utf-8")
    missing_tex = [marker for marker in TEX_MARKERS if marker not in tex]
    if missing_tex:
        fail(f"book.tex is missing expected markup: {', '.join(missing_tex)}")

    try:
        pdf_text = subprocess.run(
            ["pdftotext", str(pdf_path), "-"], check=True, text=True, capture_output=True
        ).stdout
    except FileNotFoundError:
        fail("pdftotext was not found; install poppler-utils")

    missing_pdf = [marker for marker in PDF_MARKERS if marker not in pdf_text]
    if missing_pdf:
        fail(f"book.pdf is missing expected text: {', '.join(missing_pdf)}")

    print(f"Verified {pdf_path} and {tex_path}: all expected content present.")


if __name__ == "__main__":
    main()
