"""Structural integrity and connection linter for ZettelBrain.

Runs deterministic static analysis over the knowledge base, including:
- Dead links (wikilinks pointing to missing files)
- Orphan notes (notes with no incoming references in the conceptual graph)
- Minimal connection checks (active permanent notes with fewer than 2 body links)
- References to deprecated notes
- Emergent patterns (bold terms found in 3+ notes without a corresponding note)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from config import load_settings
from logger import log_skill_execution

FRONTMATTER_PATTERN = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.DOTALL)


@dataclass
class LintError:
    """Critical integrity error, such as a dead link."""

    type: str
    file_path: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class LintWarning:
    """Improvement warning, such as an orphan note or weak graph connection."""

    type: str
    file_path: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class LintFix:
    """Automatic correction applied by the linter."""

    type: str
    file_path: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class LintResult:
    """Aggregated linter result structure."""

    errors: list[LintError] = field(default_factory=list)
    warnings: list[LintWarning] = field(default_factory=list)
    fixes: list[LintFix] = field(default_factory=list)
    emergent_patterns: list[str] = field(default_factory=list)
    total_notes: int = 0
    literature_count: int = 0
    permanent_count: int = 0
    other_count: int = 0


def slugify(text: str) -> str:
    """Convert text into a filename-friendly slug.

    Args:
        text: Input text.

    Returns:
        Slugified text.

    """
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def parse_frontmatter_and_body(content: str) -> tuple[dict[str, Any], str]:
    """Parse a note's YAML front matter and Markdown body.

    Args:
        content: Markdown file content.

    Returns:
        Parsed front matter metadata and body text.

    Raises:
        yaml.YAMLError: If the front matter block contains invalid YAML.

    """
    frontmatter: dict[str, Any] = {}
    body = content

    match = FRONTMATTER_PATTERN.match(content)
    if match:
        yaml_text = match.group(1)
        body = content[match.end() :].strip()
        parsed = yaml.safe_load(yaml_text) or {}

        if isinstance(parsed, dict):
            frontmatter = {
                str(key): _normalize_frontmatter_value(value) for key, value in parsed.items()
            }

    return frontmatter, body


def _normalize_frontmatter_value(value: Any) -> Any:
    """Preserve compatibility with the previous parser after YAML parsing.

    Args:
        value: Parsed YAML value.

    Returns:
        A normalized scalar or list value.

    """
    if isinstance(value, bool):
        return value
    if isinstance(value, list):
        return _normalize_frontmatter_list(value)
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _normalize_frontmatter_list(values: list[Any]) -> list[Any]:
    normalized: list[Any] = []
    for item in values:
        if isinstance(item, list):
            normalized.extend(_normalize_frontmatter_list(item))
        else:
            normalized.append(_normalize_frontmatter_value(item))
    return normalized


def _normalize_wikilink_target(value: str) -> str | None:
    """Normalize a wikilink-like value into its target slug.

    Args:
        value: Raw source/frontmatter string.

    Returns:
        str | None: The normalized target slug, without alias or brackets.

    """
    stripped = value.strip()
    match = re.fullmatch(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", stripped)
    if match:
        return match.group(1).strip() or None

    cleaned = stripped.strip("[").strip("]")
    target = cleaned.split("|", 1)[0].strip()
    return target or None


def expected_literature_filename(frontmatter: dict[str, Any]) -> str | None:
    """Return the expected filename for source-specific literature notes.

    Args:
        frontmatter: Parsed front matter dictionary.

    Returns:
        Expected filename with extension, or None when the note is outside the
        configured source-specific rules.

    """
    source_kind = str(frontmatter.get("source_kind", "")).strip()
    title = str(frontmatter.get("title", "")).strip()
    title_slug = slugify(title)
    if not title_slug:
        return None

    if source_kind == "youtube_transcript":
        author_slug = slugify(_first_frontmatter_value(frontmatter.get("authors")))
        if not author_slug:
            return None
        return f"youtube-{author_slug}-{title_slug}.md"

    if source_kind in {"web_article", "article"}:
        return f"article-{title_slug}.md"

    return None


def _first_frontmatter_value(value: Any) -> str:
    """Extract the first meaningful scalar from a front matter value."""
    if isinstance(value, list):
        for item in value:
            first = _first_frontmatter_value(item)
            if first:
                return first
        return ""
    return str(value).strip() if value is not None else ""


class ZettelLinter:
    """Static linting and validation engine for ZettelBrain."""

    def __init__(self, zettelkasten_path: Path) -> None:
        """Initialize the linter with the ZettelBrain vault path.

        Args:
            zettelkasten_path: Root path of the zettelbrain/ directory.

        """
        self.zettelkasten_path = zettelkasten_path
        self.existing_files: dict[str, Path] = {}
        self.notes: dict[str, dict[str, Any]] = {}

    def scan_vault(self) -> None:
        """Scan the vault to map Markdown files and read note metadata.

        Raises:
            OSError: If traversing the vault path fails before per-file parsing starts.

        """
        self.existing_files.clear()
        self.notes.clear()

        # Map every .md file in ZettelBrain.
        for file in self.zettelkasten_path.rglob("*.md"):
            slug = file.stem
            self.existing_files[slug] = file

            # Only notes under literature/ and permanent/ receive detailed analysis.
            in_literature = "literature" in file.parts
            in_permanent = "permanent" in file.parts

            if in_literature or in_permanent:
                try:
                    content = file.read_text(encoding="utf-8")
                    frontmatter, body = parse_frontmatter_and_body(content)
                    self.notes[slug] = {
                        "path": file,
                        "relative_path": str(file.relative_to(self.zettelkasten_path)),
                        "type": "literature" if in_literature else "permanent",
                        "frontmatter": frontmatter,
                        "body": body,
                        "wikilinks": self._extract_wikilinks(body, frontmatter),
                        "bold_terms": self._extract_bold_terms(body),
                    }
                except Exception as exc:
                    # Keep scanning even when a single note cannot be read or parsed.
                    self.notes[slug] = {
                        "path": file,
                        "relative_path": str(file.relative_to(self.zettelkasten_path)),
                        "type": "literature" if in_literature else "permanent",
                        "error": str(exc),
                    }

    def apply_literature_filename_fixes(self) -> list[LintFix]:
        """Rename source-specific literature notes and update wikilinks.

        Returns:
            Automatic fixes applied during the pass.

        """
        fixes: list[LintFix] = []

        for slug, info in sorted(self.notes.items()):
            if info.get("type") != "literature" or "error" in info:
                continue

            expected_name = expected_literature_filename(info["frontmatter"])
            if not expected_name:
                continue

            current_path = info["path"]
            if current_path.name == expected_name:
                continue

            target_path = current_path.with_name(expected_name)
            if target_path.exists():
                continue

            old_relative_path = str(current_path.relative_to(self.zettelkasten_path))
            current_path.rename(target_path)
            new_slug = target_path.stem
            updated_references = self._rewrite_wikilink_references(slug, new_slug)
            new_relative_path = str(target_path.relative_to(self.zettelkasten_path))

            fixes.append(
                LintFix(
                    type="literature_filename",
                    file_path=new_relative_path,
                    message=(
                        f"Renamed literature note from {old_relative_path} "
                        f"to {new_relative_path}."
                    ),
                    details={
                        "previous_path": old_relative_path,
                        "new_path": new_relative_path,
                        "expected_filename": expected_name,
                        "old_slug": slug,
                        "new_slug": new_slug,
                        "updated_references": updated_references,
                    },
                )
            )

        return fixes

    def _rewrite_wikilink_references(self, old_slug: str, new_slug: str) -> int:
        """Rewrite wikilinks pointing at a renamed note.

        Args:
            old_slug: Previous note slug.
            new_slug: New note slug.

        Returns:
            Number of wikilink replacements.

        """
        pattern = re.compile(r"\[\[([^\]|]+)(\|[^\]]*)?\]\]")
        replacements = 0

        for file in self.zettelkasten_path.rglob("*.md"):
            content = file.read_text(encoding="utf-8")

            def replace(match: re.Match[str]) -> str:
                nonlocal replacements
                target = match.group(1).strip()
                alias = match.group(2) or ""
                if target != old_slug:
                    return match.group(0)
                replacements += 1
                return f"[[{new_slug}{alias}]]"

            updated = pattern.sub(replace, content)
            if updated != content:
                file.write_text(updated, encoding="utf-8")

        return replacements

    def _extract_wikilinks(self, body: str, frontmatter: dict[str, Any]) -> list[str]:
        """Extract unique [[wikilinks]] from a note body and front matter sources.

        Args:
            body: Markdown body text.
            frontmatter: Parsed front matter dictionary.

        Returns:
            Unique linked slugs.

        """
        wikilinks = set()

        # Extract body wikilinks.
        body_matches = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", body)
        for match in body_matches:
            wikilinks.add(match.strip())

        # Extract wikilinks from the front matter 'sources' key.
        sources = frontmatter.get("sources", [])
        if isinstance(sources, list):
            for source in sources:
                if isinstance(source, str):
                    cleaned = _normalize_wikilink_target(source)
                    if cleaned:
                        wikilinks.add(cleaned)
        elif isinstance(sources, str):
            cleaned = _normalize_wikilink_target(sources)
            if cleaned:
                wikilinks.add(cleaned)

        return sorted(list(wikilinks))

    def _extract_bold_terms(self, body: str) -> list[str]:
        """Extract terms highlighted as **bold** in the note body.

        Args:
            body: Note body text.

        Returns:
            Unique bold terms.

        """
        bold_matches = re.findall(r"\*\*([^*]+)\*\*", body)
        terms = set()
        for match in bold_matches:
            cleaned = match.strip()
            # Discard empty or very short terms to avoid false positives.
            if cleaned and len(cleaned) > 2:
                terms.add(cleaned)
        return sorted(list(terms))

    def run(self) -> LintResult:
        """Run validation and return aggregated lint results.

        Returns:
            Results from the linting process.

        """
        result = LintResult(total_notes=len(self.existing_files))

        # Count files by note type.
        for file in self.existing_files.values():
            if "literature" in file.parts:
                result.literature_count += 1
            elif "permanent" in file.parts:
                result.permanent_count += 1
            else:
                result.other_count += 1

        # Build incoming link and bold-term occurrence maps.
        incoming_links: dict[str, list[str]] = {slug: [] for slug in self.existing_files}
        bold_terms_occurrences: dict[str, list[str]] = {}

        # Map the graph.
        for source_slug, info in self.notes.items():
            if "error" in info:
                result.errors.append(
                    LintError(
                        type="parsing_error",
                        file_path=info["relative_path"],
                        message=f"Failed to read or parse the file: {info['error']}",
                    )
                )
                continue

            # Track dead links and graph connections.
            for target_slug in info["wikilinks"]:
                if target_slug not in self.existing_files:
                    msg = f"Dead link detected: [[{target_slug}]] points to a missing note."
                    result.errors.append(
                        LintError(
                            type="dead_link",
                            file_path=info["relative_path"],
                            message=msg,
                            details={"target": target_slug},
                        )
                    )
                else:
                    if target_slug not in incoming_links:
                        incoming_links[target_slug] = []
                    incoming_links[target_slug].append(source_slug)

            # Track bold terms for emergent pattern detection.
            for term in info["bold_terms"]:
                if term not in bold_terms_occurrences:
                    bold_terms_occurrences[term] = []
                bold_terms_occurrences[term].append(source_slug)

        # Validate additional graph rules.
        for slug, info in self.notes.items():
            if "error" in info:
                continue

            frontmatter = info["frontmatter"]
            is_deprecated = frontmatter.get("deprecated", False)

            # 1. Source-specific literature filename convention.
            if info["type"] == "literature":
                expected_name = expected_literature_filename(frontmatter)
                if expected_name and info["path"].name != expected_name:
                    result.warnings.append(
                        LintWarning(
                            type="literature_filename_pattern",
                            file_path=info["relative_path"],
                            message=(
                                "Literature note filename does not follow the expected "
                                f"source-specific pattern: {expected_name}."
                            ),
                            details={"expected_filename": expected_name},
                        )
                    )

            # 2. Orphan notes in the conceptual graph.
            # A literature or permanent note is orphaned when it receives no conceptual links
            # from other literature/ or permanent/ notes.
            conceptual_incoming = [
                src for src in incoming_links.get(slug, []) if src in self.notes and src != slug
            ]
            if not conceptual_incoming and slug not in {"index", "overview"}:
                msg = f"Orphan note detected: no other conceptual graph note points to [[{slug}]]."
                result.warnings.append(
                    LintWarning(
                        type="orphan_note",
                        file_path=info["relative_path"],
                        message=msg,
                    )
                )

            # 3. Minimal graph connection for active permanent notes.
            if info["type"] == "permanent" and not is_deprecated:
                # Only count wikilinks detected in the body, excluding front matter.
                body_links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", info["body"])
                body_links_unique = {link.strip() for link in body_links}
                if len(body_links_unique) < 2:
                    result.warnings.append(
                        LintWarning(
                            type="minimal_connection",
                            file_path=info["relative_path"],
                            message=(
                                f"Minimal connection: active permanent note [[{slug}]] "
                                "has fewer than two outgoing body links "
                                f"({len(body_links_unique)} detected)."
                            ),
                            details={"outgoing_count": len(body_links_unique)},
                        )
                    )

            # 4. Deprecated notes still active in the graph.
            if is_deprecated:
                active_referrers = []
                for referrer in conceptual_incoming:
                    ref_info = self.notes.get(referrer)
                    if ref_info and not ref_info["frontmatter"].get("deprecated", False):
                        active_referrers.append(referrer)

                if active_referrers:
                    superseded = frontmatter.get("superseded_by", None)
                    message = (
                        f"Deprecated note [[{slug}]] is still referenced by active notes: "
                        f"{', '.join([f'[[{r}]]' for r in active_referrers])}."
                    )
                    if not superseded:
                        message += (
                            " No replacement note (superseded_by) was provided in front matter."
                        )

                    result.warnings.append(
                        LintWarning(
                            type="deprecated_reference",
                            file_path=info["relative_path"],
                            message=message,
                            details={
                                "active_referrers": active_referrers,
                                "superseded_by": superseded,
                            },
                        )
                    )

        # 5. Emergent patterns: bold terms in 3+ notes without their own note.
        for term, occurrences in bold_terms_occurrences.items():
            unique_occurrences = list(set(occurrences))
            if len(unique_occurrences) >= 3:
                term_slug = slugify(term)
                exists = term_slug in self.existing_files
                # Also check whether any note has the exact same title.
                if not exists:
                    for info in self.notes.values():
                        title = info.get("frontmatter", {}).get("title", "")
                        if title.lower().strip() == term.lower().strip():
                            exists = True
                            break

                if not exists:
                    result.emergent_patterns.append(term)

        # Sort results for stable reports.
        result.errors.sort(key=lambda x: (x.file_path, x.message))
        result.warnings.sort(key=lambda x: (x.file_path, x.message))
        result.emergent_patterns.sort()

        return result


def print_text_report(result: LintResult) -> None:
    """Print a human-readable text report to the console.

    Args:
        result: Aggregated lint result structure.

    """
    print("=" * 60)
    print("ZETTELBRAIN HEALTH AND INTEGRITY REPORT")
    print("=" * 60)
    print(f"Total cataloged notes: {result.total_notes}")
    print(f"  - Literature notes: {result.literature_count}")
    print(f"  - Permanent notes:  {result.permanent_count}")
    print(f"  - Other files:      {result.other_count}")
    print("-" * 60)

    if result.errors:
        print(f"\n[CRITICAL ERRORS] Found {len(result.errors)} errors:")
        for err in result.errors:
            print(f"  - [{err.type.upper()}] in {err.file_path}:")
            print(f"    {err.message}")
    else:
        print("\n[OK] No critical structural integrity errors found.")

    if result.warnings:
        print(f"\n[IMPROVEMENT WARNINGS] Found {len(result.warnings)} warnings:")
        for warn in result.warnings:
            print(f"  - [{warn.type.upper()}] in {warn.file_path}:")
            print(f"    {warn.message}")
    else:
        print("\n[OK] No pending improvement warnings.")

    if result.fixes:
        print(f"\n[AUTOMATIC FIXES] Applied {len(result.fixes)} fixes:")
        for fix in result.fixes:
            print(f"  - [{fix.type.upper()}] in {fix.file_path}:")
            print(f"    {fix.message}")
    else:
        print("\n[OK] No automatic fixes applied.")

    if result.emergent_patterns:
        print("\n[EMERGENT PATTERNS] Permanent note candidates found in 3+ distinct notes:")
        for pattern in result.emergent_patterns:
            print(f"  - **{pattern}**")
    else:
        print("\n[OK] No emergent patterns identified.")

    print("=" * 60)


def run_linter(zettelkasten_path: Path, *, fix_filenames: bool = True) -> LintResult:
    """Run the linter, optionally applying deterministic filename fixes first.

    Args:
        zettelkasten_path: Root path of the zettelbrain/ directory.
        fix_filenames: Whether to rename source-specific literature notes.

    Returns:
        Aggregated lint results, including fixes applied before validation.

    """
    linter = ZettelLinter(zettelkasten_path)
    linter.scan_vault()
    fixes = linter.apply_literature_filename_fixes() if fix_filenames else []

    if fixes:
        linter.scan_vault()

    result = linter.run()
    result.fixes.extend(fixes)
    result.fixes.sort(key=lambda x: (x.file_path, x.message))
    return result


def lint_result_to_dict(result: LintResult) -> dict[str, Any]:
    """Serialize lint results to a JSON-compatible dictionary."""
    return {
        "total_notes": result.total_notes,
        "literature_count": result.literature_count,
        "permanent_count": result.permanent_count,
        "other_count": result.other_count,
        "errors": [asdict(e) for e in result.errors],
        "warnings": [asdict(w) for w in result.warnings],
        "fixes": [asdict(f) for f in result.fixes],
        "emergent_patterns": result.emergent_patterns,
    }


@log_skill_execution
def run_lint_logic() -> dict[str, Any]:
    """Run linting logic using the configured vault.

    Returns:
        Dictionary representation of lint results.

    """
    settings = load_settings()
    result = run_linter(settings.zettelkasten_path, fix_filenames=True)

    return lint_result_to_dict(result)


def main() -> None:
    """Command-line interface entry point.

    Runs linting, formats output according to CLI arguments, and sets the
    appropriate process exit code.
    """
    parser = argparse.ArgumentParser(description="Static integrity linter for ZettelBrain.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Return the result as compact JSON.",
    )
    parser.add_argument(
        "--no-fix",
        action="store_true",
        help="Report literature filename convention issues without renaming files.",
    )
    args = parser.parse_args()

    try:
        settings = load_settings()
        result = run_linter(settings.zettelkasten_path, fix_filenames=not args.no_fix)

        if args.json:
            print(json.dumps(lint_result_to_dict(result), ensure_ascii=False, indent=2))
        else:
            print_text_report(result)

        # Critical errors, such as dead links or parsing failures, return status 1.
        if result.errors:
            sys.exit(1)
        sys.exit(0)

    except Exception as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        else:
            print(f"[CRITICAL ERROR] Linter execution failed: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
