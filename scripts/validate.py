#!/usr/bin/env python3
"""Fast, deterministic validation for author-controlled book inputs."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
NOTES = ROOT / "notes"
IMAGE_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".pdf"}
errors: list[str] = []


def report(path: Path | str, message: str) -> None:
    try:
        shown = Path(path).resolve().relative_to(ROOT)
    except (ValueError, TypeError):
        shown = path
    errors.append(f"{shown}: {message}")


def slug(text: str) -> str:
    text = re.sub(r"[`*_~]", "", text).strip().lower()
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    return re.sub(r"[-\s]+", "-", text).strip("-")


FENCE_LINE = re.compile(r"^\s*(```|~~~)")


def strip_fenced_blocks(text: str) -> str:
    """Blank out fenced code block bodies so code samples (generics like
    List<String>, shell backslashes, literal `{=latex}` in a teaching
    example, ...) cannot trip the raw-HTML/raw-TeX trust-boundary checks."""
    out: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if FENCE_LINE.match(line):
            in_fence = not in_fence
            out.append("")
        else:
            out.append("" if in_fence else line)
    return "\n".join(out)


def headings(text: str) -> set[str]:
    result: set[str] = set()
    in_fence = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            in_fence = not in_fence
        elif not in_fence and (match := re.match(r"^#{1,6}\s+(.+?)\s*$", line)):
            title = re.sub(r"\s+\{[^}]*\}\s*$", "", match.group(1))
            result.add(slug(title))
    return result


def main() -> int:
    config_path = ROOT / "book.yml"
    schema_path = ROOT / "schema/book.schema.json"
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        schema = __import__("json").loads(schema_path.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(config)
    except (OSError, yaml.YAMLError, jsonschema.ValidationError, ValueError) as exc:
        report(config_path, f"configuration is invalid: {exc}")
        print("\n".join(errors), file=sys.stderr)
        return 1

    chapters = [ROOT / item for item in config["chapters"]]
    configured = {p.resolve() for p in chapters}
    discovered = {p.resolve() for p in NOTES.rglob("*.md")}
    for path in sorted(discovered - configured):
        report(path, "Markdown chapter is not listed in book.yml")
    for path in sorted(configured - discovered):
        report(path, "configured chapter does not exist")

    used_assets: set[Path] = set()
    labels: dict[str, Path] = {}
    documents: dict[Path, tuple[str, set[str]]] = {}
    for path in chapters:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        documents[path.resolve()] = (text, headings(text))
        meaningful = re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()
        if not meaningful:
            report(path, "chapter is empty")
        top = re.findall(r"^#\s+\S.*$", text, flags=re.M)
        if len(top) != 1:
            report(path, f"chapter must contain exactly one level-one heading (found {len(top)})")

        # Raw input is intentionally excluded from the repository's trust
        # boundary. Fenced code blocks (including mermaid diagrams, which
        # use the same ``` fences) are exempt so genuine code samples don't
        # trip these checks.
        scannable = strip_fenced_blocks(text)
        if re.search(r"<\/?[A-Za-z][^>]*>", scannable):
            report(path, "raw HTML is not allowed outside fenced code blocks")
        if re.search(r"(?<!`)\\(?:input|include|write18|usepackage|documentclass|begin|end)\b", scannable):
            report(path, "raw LaTeX command is not allowed outside fenced code blocks")
        if re.search(r"\{=(?:latex|tex|html)\}", scannable, flags=re.I):
            report(path, "raw format attributes are not allowed outside fenced code blocks")

        for label in re.findall(r"\{[^}\n]*#(fig:[A-Za-z0-9_.:-]+)[^}\n]*\}", text):
            if label in labels:
                report(path, f"duplicate figure label {label!r}; first used in {labels[label].relative_to(ROOT)}")
            else:
                labels[label] = path

        # Inline images; remote images and data URIs are deliberately unsupported.
        for target in re.findall(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)", text):
            target = unquote(target.split("#", 1)[0])
            if "://" in target or target.startswith(("data:", "/")):
                report(path, f"image path must be local and relative: {target}")
                continue
            asset = (path.parent / target).resolve()
            try:
                asset.relative_to(NOTES.resolve())
            except ValueError:
                report(path, f"image escapes notes/: {target}")
                continue
            used_assets.add(asset)
            if asset.suffix.lower() not in IMAGE_EXTENSIONS:
                report(path, f"unsupported image type: {target}")
            if not asset.is_file():
                report(path, f"missing image: {target}")

        definitions = set(re.findall(r"^\[([^\]^]+)\]:\s+\S+", text, flags=re.M | re.I))
        ref_uses = set(re.findall(r"(?<!!)\[[^\]]+\]\[([^\]]+)\]", text))
        for ref in sorted(ref_uses - definitions):
            report(path, f"undefined Markdown reference [{ref}]")
        foot_defs = set(re.findall(r"^\[\^([^\]]+)\]:", text, flags=re.M))
        foot_uses = set(re.findall(r"\[\^([^\]]+)\]", re.sub(r"^\[\^[^\]]+\]:.*$", "", text, flags=re.M)))
        for ref in sorted(foot_uses - foot_defs):
            report(path, f"undefined footnote [^{ref}]")
        for ref in sorted(foot_defs - foot_uses):
            report(path, f"unused footnote definition [^{ref}]")

    all_assets = {p.resolve() for p in (NOTES / "assets").rglob("*") if p.is_file()}
    for path in sorted(all_assets - used_assets):
        report(path, "orphaned asset is not referenced by a chapter")

    # Validate inline Markdown links after all heading inventories are available.
    for path_key, (text, own_headings) in documents.items():
        path = Path(path_key)
        for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)", text):
            if re.match(r"(?:https?|mailto):", target):
                continue
            raw_path, _, fragment = unquote(target).partition("#")
            destination = (path.parent / raw_path).resolve() if raw_path else path.resolve()
            if not destination.is_file():
                report(path, f"broken internal link: {target}")
                continue
            if fragment:
                if destination in documents:
                    available = documents[destination][1]
                elif destination.suffix.lower() == ".md":
                    available = headings(destination.read_text(encoding="utf-8"))
                else:
                    available = set()
                if slug(fragment) not in available:
                    report(path, f"broken heading fragment: {target}")

    if errors:
        print("Validation failed:", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"Validation passed: {len(chapters)} chapters, {len(used_assets)} assets, {len(labels)} figure labels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
