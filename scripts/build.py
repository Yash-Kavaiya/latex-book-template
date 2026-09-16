#!/usr/bin/env python3
"""Validate book.yml and render it with Pandoc without evaluating configuration."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]

DEFAULTS = {
    "subtitle": "", "authors": [], "language": "en-US", "date": "",
    "description": "", "cover_image": None, "paper_size": "a4",
    "fonts": {"main": "Libertinus Serif", "sans": "Libertinus Sans", "mono": "Libertinus Mono", "size": "11pt"},
    "margins": {"top": "25mm", "right": "25mm", "bottom": "25mm", "left": "25mm"},
    "link_colors": {"link": "blue", "url": "blue", "cite": "green"},
    "document_class_options": ["openany"], "page_numbering": "arabic",
    "header_text": "", "footer_text": "", "table_of_contents": True,
    "list_of_figures": False, "list_of_tables": False,
}


def latex_escape(value: str) -> str:
    """Escape untrusted text used directly in the LaTeX template."""
    replacements = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in value)


def load_config(path: Path) -> tuple[dict, list[Path]]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read YAML: {exc}") from exc
    schema = json.loads((ROOT / "config/book.schema.json").read_text(encoding="utf-8"))
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
    authors = config["authors"] or ([config["author"]] if config.get("author") else [])
    escaped = lambda key: latex_escape(config[key])
    colors = config["link_colors"]
    return {
        "title": escaped("title"), "subtitle": escaped("subtitle"),
        "authors": r" \and ".join(map(latex_escape, authors)), "lang": config["language"],
        "date": escaped("date"), "description": escaped("description"),
        "cover-image": config["cover_image"], "paper-size": config["paper_size"],
        "document-class": "book", "class-options": ",".join(config["document_class_options"]),
        "main-font": latex_escape(config["fonts"]["main"]), "sans-font": latex_escape(config["fonts"]["sans"]),
        "mono-font": latex_escape(config["fonts"]["mono"]), "font-size": config["fonts"]["size"],
        **{f"margin-{key}": value for key, value in config["margins"].items()},
        **{f"{key}-color": value for key, value in colors.items()},
        **{f"{key}-color-hex": len(value) == 6 for key, value in colors.items()},
        "page-numbering": config["page_numbering"], "header-text": escaped("header_text"),
        "footer-text": escaped("footer_text"), "table-of-contents": config["table_of_contents"],
        "list-of-figures": config["list_of_figures"], "list-of-tables": config["list_of_tables"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "book.yml")
    parser.add_argument("--output", type=Path, default=ROOT / "build/book.pdf")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        config, chapters = load_config(args.config)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    if args.validate_only:
        print(f"Valid configuration: {args.config}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as metadata_file:
        json.dump(metadata(config), metadata_file)
        metadata_file.flush()
        command = ["pandoc", *map(str, chapters), "--metadata-file", metadata_file.name,
                   "--template", str(ROOT / "templates/book.tex"), "--pdf-engine=xelatex", "-o", str(args.output)]
        try:
            subprocess.run(command, cwd=args.config.resolve().parent, check=True)
        except FileNotFoundError:
            print("Rendering error: pandoc is not installed", file=sys.stderr)
            return 127
        except subprocess.CalledProcessError as exc:
            return exc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
