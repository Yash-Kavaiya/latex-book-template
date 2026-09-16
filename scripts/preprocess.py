#!/usr/bin/env python3
"""Validate book.yaml and prepare chapters and Mermaid images for Pandoc."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml


IMAGE = re.compile(r"(!\[[^]]*\]\()([^\s)]+)([^)]*\))")
MERMAID = re.compile(r"```mermaid[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE)


def fail(message: str) -> "NoReturn":
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    if len(sys.argv) != 3:
        fail("usage: preprocess.py CONFIG OUTPUT_DIRECTORY")
    config = Path(sys.argv[1]).resolve()
    root = config.parent
    output = Path(sys.argv[2]).resolve()
    try:
        data = yaml.safe_load(config.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"invalid configuration {config}: {exc}")
    if not isinstance(data, dict):
        fail("configuration must be a YAML mapping")
    chapters = data.get("chapters")
    if not isinstance(chapters, list):
        fail("configuration key 'chapters' must be an array")
    if not chapters:
        fail("chapter list is empty; add Markdown paths to 'chapters' in book.yaml")
    if any(not isinstance(item, str) or not item.strip() for item in chapters):
        fail("every chapter entry must be a non-empty path string")

    chapter_dir = output / "chapters"
    diagram_dir = output / "diagrams"
    chapter_dir.mkdir(parents=True)
    diagram_dir.mkdir(parents=True)
    puppeteer_config = output / "puppeteer-config.json"
    puppeteer_config.write_text(
        json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}),
        encoding="utf-8",
    )
    prepared: list[str] = []

    for chapter_number, item in enumerate(chapters, 1):
        source = (root / item).resolve()
        notes = (root / "notes").resolve()
        if notes not in source.parents:
            fail(f"chapter must be inside notes/: {item}")
        if source.suffix.lower() not in {".md", ".markdown"}:
            fail(f"chapter is not Markdown: {item}")
        if not source.is_file():
            fail(f"chapter source does not exist: {item}")
        text = source.read_text(encoding="utf-8")

        def render(match: re.Match[str]) -> str:
            diagram_number = render.count
            render.count += 1
            stem = f"chapter-{chapter_number:03d}-{diagram_number:03d}"
            definition = diagram_dir / f"{stem}.mmd"
            image = diagram_dir / f"{stem}.pdf"
            definition.write_text(match.group(1), encoding="utf-8")
            command = [
                "mmdc", "-p", str(puppeteer_config), "-i", str(definition),
                "-o", str(image), "-b", "transparent",
            ]
            result = subprocess.run(command, text=True, capture_output=True)
            if result.returncode or not image.is_file():
                detail = (result.stderr or result.stdout).strip()
                fail(f"diagram rendering failed in {item}: {detail or 'mmdc produced no output'}")
            return f"![Diagram]({image})"

        render.count = 1
        text = MERMAID.sub(render, text)

        def resolve_image(match: re.Match[str]) -> str:
            target = match.group(2)
            if re.match(r"(?:[a-z]+:|#)", target, re.IGNORECASE):
                return match.group(0)
            asset = (source.parent / target).resolve()
            if not asset.is_file():
                fail(f"unresolved asset '{target}' referenced by {item}")
            return f"{match.group(1)}{asset}{match.group(3)}"

        text = IMAGE.sub(resolve_image, text)
        destination = chapter_dir / f"{chapter_number:03d}-{source.name}"
        destination.write_text(text, encoding="utf-8")
        prepared.append(str(destination))

    (output / "chapter-list.txt").write_text("\n".join(prepared) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
