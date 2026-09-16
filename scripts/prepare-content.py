#!/usr/bin/env python3
"""Prepare Markdown files for the book build.

Image and Mermaid references are made deterministic here, before Pandoc sees
them.  In particular, paths are resolved against the file which contains the
reference (not the directory in which the build happened).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

IMAGE = re.compile(
    r"!\[(?P<caption>[^]]*)\]\((?:<(?P<angle>[^>]+)>|(?P<plain>[^)]+))\)"
    r"(?P<attrs>\{[^}\n]*\})?"
)
FENCE = re.compile(
    r"^```mermaid(?:\s+(?P<attrs>\{[^}]*\}))?\s*\n(?P<body>.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)
ATTR = re.compile(r'''(?P<key>#[\w:.-]+|[\w-]+)(?:=(?P<q>["'])(?P<quoted>.*?)\2|=(?P<bare>[^\s]+))?''')


def latex_escape(value: str) -> str:
    """Escape untrusted plain text for a LaTeX argument."""
    replacements = {
        "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}",
        "$": r"\$", "&": r"\&", "#": r"\#", "%": r"\%",
        "_": r"\_", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in value)


def parse_attrs(raw: str | None) -> dict[str, str]:
    values: dict[str, str] = {}
    for match in ATTR.finditer((raw or "").strip("{} ")):
        key = match.group("key")
        value = match.group("quoted") or match.group("bare") or "true"
        if key.startswith("#"):
            values["label"] = key[1:]
        else:
            values[key.lower()] = value
    return values


def safe_label(label: str) -> str:
    # Labels are control-sequence-adjacent input: use a strict allow list.
    return re.sub(r"[^A-Za-z0-9:._-]", "-", label)


def dimension(value: str | None, default: str) -> str:
    if not value:
        return default
    value = value.strip()
    if re.fullmatch(r"\d+(?:\.\d+)?%", value):
        return f"{min(float(value[:-1]) / 100, 1):g}\\linewidth"
    if re.fullmatch(r"\d+(?:\.\d+)?(?:pt|mm|cm|in|em|ex|\\linewidth|\\textwidth)", value):
        return value
    # Never copy arbitrary configuration into TeX.
    return default


def asset_name(source: Path, suffix: str | None = None) -> str:
    digest = hashlib.sha256(str(source.resolve()).encode()).hexdigest()[:12]
    stem = re.sub(r"[^A-Za-z0-9._-]", "-", source.stem).strip(".-") or "asset"
    return f"{stem}-{digest}{suffix or source.suffix.lower()}"


def figure(path: str | None, caption: str, attrs: dict[str, str], missing: str | None = None) -> str:
    align = attrs.get("align", "center").lower()
    placement = {"left": "flushleft", "right": "flushright"}.get(align, "center")
    width = dimension(attrs.get("width"), r"\linewidth")
    height = dimension(attrs.get("height"), r"0.85\textheight")
    lines = [r"\begin{figure}[htbp]", {"center": r"\centering", "flushleft": r"\raggedright", "flushright": r"\raggedleft"}[placement]]
    if missing:
        lines.append(r"\fbox{\parbox{0.9\linewidth}{\textbf{Missing image:} " + latex_escape(missing) + "}}")
    else:
        # detokenize prevents TeX-special characters in a controlled relative path.
        lines.append(r"\adjustbox{max width=\linewidth,max totalheight=0.85\textheight}{\includegraphics[width=" + width + ",height=" + height + r",keepaspectratio]{\detokenize{" + path + "}}}")
    if caption:
        lines.append(r"\caption{" + latex_escape(caption) + "}")
    if attrs.get("label"):
        lines.append(r"\label{" + safe_label(attrs["label"]) + "}")
    lines.append(r"\end{figure}")
    return "\n".join(lines)


class Preparer:
    def __init__(self, assets: Path, renderer: list[str], strict: bool, svg_converter: list[str] | None = None):
        self.assets = assets
        self.renderer = renderer
        self.strict = strict
        self.svg_converter = svg_converter or ["rsvg-convert", "-f", "pdf"]
        assets.mkdir(parents=True, exist_ok=True)
        self._puppeteer_config: Path | None = None

    def _mermaid_puppeteer_config(self) -> Path:
        # CI containers commonly lack unprivileged user namespaces (AppArmor
        # restricts them on newer Ubuntu), which breaks Chromium's sandbox.
        # --no-sandbox is standard practice for headless Chrome in CI.
        if self._puppeteer_config is None:
            config = self.assets.parent / "mermaid-puppeteer-config.json"
            config.write_text(
                json.dumps({"args": ["--no-sandbox", "--disable-setuid-sandbox"]}),
                encoding="utf-8",
            )
            self._puppeteer_config = config
        return self._puppeteer_config

    def image(self, match: re.Match[str], source: Path) -> str:
        raw = (match.group("angle") or match.group("plain")).strip()
        # Optional Markdown title is deliberately not interpreted as a path.
        if match.group("plain") and re.search(r'''\s+["'][^"']*["']$''', raw):
            raw = re.sub(r'''\s+["'][^"']*["']$''', "", raw)
        candidate = (source.parent / raw).resolve()
        attrs = parse_attrs(match.group("attrs"))
        if not candidate.is_file():
            message = f"{source}: image not found: {raw}"
            if self.strict:
                raise FileNotFoundError(message)
            print(f"warning: {message}", file=sys.stderr)
            return figure(None, match.group("caption"), attrs, raw)
        if candidate.suffix.lower() == ".svg":
            # XeLaTeX/graphicx cannot embed SVG directly; rasterizing it to a
            # vector PDF up front keeps \includegraphics simple and portable.
            target = self.assets / asset_name(candidate, ".pdf")
            if not target.exists():
                result = subprocess.run(
                    self.svg_converter + ["-o", str(target), str(candidate)],
                    text=True, capture_output=True,
                )
                if result.returncode or not target.is_file():
                    detail = (result.stderr or result.stdout).strip()
                    message = f"{source}: could not convert {raw} to PDF: {detail or 'no output'}"
                    if self.strict:
                        raise RuntimeError(message)
                    print(f"warning: {message}", file=sys.stderr)
                    return figure(None, match.group("caption"), attrs, raw)
        else:
            target = self.assets / asset_name(candidate)
            shutil.copy2(candidate, target)
        return figure(target.as_posix(), match.group("caption"), attrs)

    def mermaid(self, match: re.Match[str], source: Path) -> str:
        attrs = parse_attrs(match.group("attrs"))
        body = match.group("body")
        digest = hashlib.sha256((body + "\0" + str(source)).encode()).hexdigest()[:16]
        definition = self.assets / f"mermaid-{digest}.mmd"
        output = self.assets / f"mermaid-{digest}.pdf"
        definition.write_text(body, encoding="utf-8")
        if not output.exists():
            # A list and shell=False ensure diagram/configuration text can never
            # become a shell command.
            subprocess.run(
                self.renderer + [
                    "-p", str(self._mermaid_puppeteer_config()),
                    "-i", str(definition), "-o", str(output), "-b", "transparent",
                ],
                check=True,
            )
        caption = attrs.pop("caption", "")
        return figure(output.as_posix(), caption, attrs)

    def prepare(self, source: Path) -> str:
        text = source.read_text(encoding="utf-8")
        text = FENCE.sub(lambda match: self.mermaid(match, source), text)
        return IMAGE.sub(lambda match: self.image(match, source), text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--assets-dir", required=True, type=Path)
    parser.add_argument("--strict", action="store_true", help="fail rather than typeset a missing-image notice")
    parser.add_argument("--mermaid-command", nargs="+", default=["npx", "--no-install", "mmdc"])
    parser.add_argument("--svg-converter", nargs="+", default=["rsvg-convert", "-f", "pdf"])
    args = parser.parse_args()
    preparer = Preparer(args.assets_dir, args.mermaid_command, args.strict, args.svg_converter)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sections = [preparer.prepare(path) for path in args.inputs]
    args.output.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
