#!/usr/bin/env python3
"""Render Mermaid fences and produce the combined Markdown consumed by Pandoc."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "mermaid"
FENCE = re.compile(
    r'^```\{\.mermaid\s+#(?P<label>fig:[\w.:-]+)\s+caption="(?P<caption>[^"]+)"\}\s*\n'
    r"(?P<body>.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)


def main() -> None:
    config = yaml.safe_load((ROOT / "book.yml").read_text(encoding="utf-8"))
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    combined: list[str] = []
    for chapter_name in config["chapters"]:
        chapter = ROOT / chapter_name
        text = chapter.read_text(encoding="utf-8")

        def replace(match: re.Match[str]) -> str:
            stem = match.group("label").replace(":", "-")
            source = OUT / f"{stem}.mmd"
            image = OUT / f"{stem}.svg"
            source.write_text(match.group("body").rstrip() + "\n", encoding="utf-8")
            subprocess.run(
                ["npx", "--no-install", "mmdc", "-i", str(source), "-o", str(image), "-b", "transparent"],
                cwd=ROOT,
                check=True,
            )
            return f'![{match.group("caption")}](build/mermaid/{image.name}){{#{match.group("label")} width=90%}}'

        combined.append(FENCE.sub(replace, text))
    (ROOT / "build" / "book.md").write_text("\n\n".join(combined) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
