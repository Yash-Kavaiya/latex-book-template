#!/usr/bin/env python3
"""Validate book.yml and turn it into a Pandoc metadata file.

Configuration is data, never code: every value that ends up in the LaTeX
template is either LaTeX-escaped plain text or drawn from a strict schema
allow-list (colors, paper size, document-class options, ...). This keeps
book.yml from ever being able to inject a LaTeX command, document class,
or shell-escape.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]

DEFAULTS = {
    "subtitle": "", "language": "en-US", "date": "", "description": "",
    "cover_image": None, "paper_size": "a4",
    "fonts": {"main": "TeX Gyre Pagella", "sans": "TeX Gyre Heros", "mono": "TeX Gyre Cursor", "size": "11pt"},
    "margins": {"top": "25mm", "right": "25mm", "bottom": "25mm", "left": "25mm"},
    "link_colors": {"link": "blue", "url": "blue", "cite": "teal"},
    "document_class_options": ["openany"], "page_numbering": "arabic",
    "header_text": "", "footer_text": "", "toc_depth": 2,
    "table_of_contents": True, "list_of_figures": False, "list_of_tables": False,
}


def latex_escape(value: str) -> str:
    """Escape untrusted plain text used directly in the LaTeX template."""
    replacements = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def load_config(path: Path) -> tuple[dict, list[Path]]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("configuration must be a YAML mapping")

    schema = json.loads((ROOT / "schema/book.schema.json").read_text(encoding="utf-8"))
    try:
        jsonschema.Draft202012Validator(schema).validate(raw)
    except jsonschema.ValidationError as exc:
        location = ".".join(map(str, exc.absolute_path)) or "book.yml"
        raise ValueError(f"{location}: {exc.message}") from exc

    config = DEFAULTS | raw
    config["fonts"] = DEFAULTS["fonts"] | raw.get("fonts", {})
    config["margins"] = DEFAULTS["margins"] | raw.get("margins", {})
    config["link_colors"] = DEFAULTS["link_colors"] | raw.get("link_colors", {})
    base = path.resolve().parent

    def checked_asset(name: str, value: str) -> Path:
        candidate = (base / value).resolve()
        if not candidate.is_relative_to(base) or not candidate.is_file():
            raise ValueError(f"{name}: file is missing, inaccessible, or outside the book directory: {value}")
        return candidate

    chapters = [checked_asset("chapters", item) for item in config["chapters"]]
    if config["cover_image"]:
        checked_asset("cover_image", config["cover_image"])
    return config, chapters


def metadata(config: dict) -> dict:
    author = config["author"]
    authors = author if isinstance(author, list) else [author]
    colors = config["link_colors"]
    return {
        "title": latex_escape(config["title"]),
        "subtitle": latex_escape(config["subtitle"]),
        "authors": r" \and ".join(latex_escape(item) for item in authors),
        "lang": config["language"],
        "date": latex_escape(config["date"]),
        "description": latex_escape(config["description"]),
        "cover-image": config["cover_image"],
        "paper-size": config["paper_size"],
        "class-options": ",".join(config["document_class_options"]),
        "main-font": config["fonts"]["main"], "sans-font": config["fonts"]["sans"],
        "mono-font": config["fonts"]["mono"], "font-size": config["fonts"]["size"],
        **{f"margin-{key}": value for key, value in config["margins"].items()},
        **{f"{key}-color": value for key, value in colors.items()},
        **{f"{key}-color-hex": len(value) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in value) for key, value in colors.items()},
        "page-numbering": config["page_numbering"],
        "header-text": latex_escape(config["header_text"]),
        "footer-text": latex_escape(config["footer_text"]),
        "toc-depth": config["toc_depth"],
        "table-of-contents": config["table_of_contents"],
        "list-of-figures": config["list_of_figures"],
        "list-of-tables": config["list_of_tables"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "book.yml")
    parser.add_argument("--validate-only", action="store_true", help="check book.yml and exit")
    parser.add_argument("--metadata-out", type=Path, help="write the Pandoc metadata JSON file here")
    parser.add_argument("--chapters-out", type=Path, help="write the resolved, ordered chapter paths here, one per line")
    args = parser.parse_args()

    try:
        config, chapters = load_config(args.config)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    if args.validate_only:
        print(f"Valid configuration: {args.config}")
        return 0

    if args.metadata_out:
        args.metadata_out.parent.mkdir(parents=True, exist_ok=True)
        args.metadata_out.write_text(json.dumps(metadata(config), indent=2), encoding="utf-8")
        print(f"Wrote {args.metadata_out}")

    if args.chapters_out:
        args.chapters_out.parent.mkdir(parents=True, exist_ok=True)
        args.chapters_out.write_text("\n".join(str(path) for path in chapters) + "\n", encoding="utf-8")
        print(f"Wrote {args.chapters_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
