#!/usr/bin/env python3
"""
memory_health.py — Claude Code auto-memory health analyzer.

Reads ~/.claude/projects/<path>/memory/ and reports:
  - Line count vs. 200-line limit
  - Topic file inventory
  - Stale entries (references files not on disk)
  - Promotion candidates (patterns mentioned 3+ times across sessions)
  - Consolidation opportunities (related entries)

Usage:
    python scripts/memory_health.py
    python scripts/memory_health.py ~/.claude/projects/my-project/memory/
    python scripts/memory_health.py --output json
    python scripts/memory_health.py --filter promotions
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


MEMORY_LIMIT = 200  # Claude Code loads only first 200 lines of MEMORY.md


@dataclass
class MemoryEntry:
    """A single bullet/section in MEMORY.md."""
    line: int
    text: str
    category: Optional[str] = None  # Inferred from heading


@dataclass
class HealthReport:
    memory_path: str
    main_file_lines: int
    main_file_exists: bool
    topic_files: List[str] = field(default_factory=list)
    entries: List[MemoryEntry] = field(default_factory=list)
    stale_entries: List[MemoryEntry] = field(default_factory=list)
    promotion_candidates: List[Tuple[str, int]] = field(default_factory=list)  # (pattern, count)
    consolidation_groups: List[List[MemoryEntry]] = field(default_factory=list)

    @property
    def utilization_pct(self) -> float:
        if not self.main_file_exists:
            return 0.0
        return min(100.0, (self.main_file_lines / MEMORY_LIMIT) * 100)

    @property
    def is_near_limit(self) -> bool:
        return self.main_file_lines >= MEMORY_LIMIT * 0.85

    @property
    def is_over_limit(self) -> bool:
        return self.main_file_lines > MEMORY_LIMIT


def find_memory_dir(cwd: str) -> Optional[str]:
    """
    Auto-detect Claude Code memory directory for the given project path.
    Converts: /Users/alice/code/myapp → ~/.claude/projects/-Users-alice-code-myapp/memory/
    """
    home = str(Path.home())
    # Claude Code encodes the path as dash-separated (absolute path, slashes→dashes)
    encoded = cwd.replace("/", "-").lstrip("-")
    candidate = os.path.join(home, ".claude", "projects", encoded, "memory")
    if os.path.isdir(candidate):
        return candidate
    return None


def parse_memory_file(path: str) -> List[MemoryEntry]:
    """Parse MEMORY.md into MemoryEntry objects, tracking heading context."""
    entries = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return entries

    current_category = None
    for lineno, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            # Heading — update current category
            current_category = re.sub(r"^#+\s*", "", line).strip()
            continue
        if line.startswith("- ") or line.startswith("* "):
            text = line[2:].strip()
            entries.append(MemoryEntry(line=lineno, text=text, category=current_category))

    return entries


def detect_stale_entries(entries: List[MemoryEntry], project_root: str) -> List[MemoryEntry]:
    """
    Find entries that reference file paths which no longer exist on disk.
    Looks for patterns like `path/to/file.ts` or backtick paths.
    """
    stale = []
    path_pattern = re.compile(r"[`'\"]?([\w./\-]+\.(ts|js|py|go|rs|json|yaml|yml|md))[`'\"]?")

    for entry in entries:
        m = path_pattern.search(entry.text)
        if m:
            referenced = m.group(1)
            # Only check relative paths (not absolute)
            if not referenced.startswith("/"):
                full = os.path.join(project_root, referenced)
                if not os.path.exists(full):
                    stale.append(entry)

    return stale


def detect_promotion_candidates(entries: List[MemoryEntry], threshold: int = 2) -> List[Tuple[str, int]]:
    """
    Find recurring concepts across entries — these are worth promoting to CLAUDE.md.
    Uses keyword frequency (noun phrases, commands, tool names).
    """
    # Extract key phrases: words that appear near "always", "never", "use", "prefer", "avoid"
    rule_indicators = re.compile(
        r"\b(always|never|prefer|avoid|use|don'?t|must|should|remember|note)\b",
        re.IGNORECASE,
    )
    # Build ngrams from entries that contain rule-like language
    phrase_counter: Counter = Counter()

    for entry in entries:
        if rule_indicators.search(entry.text):
            # Extract 2-3 word key phrases
            words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_\-]{2,}\b", entry.text)
            for i in range(len(words) - 1):
                bigram = f"{words[i].lower()} {words[i+1].lower()}"
                phrase_counter[bigram] += 1
            for i in range(len(words) - 2):
                trigram = f"{words[i].lower()} {words[i+1].lower()} {words[i+2].lower()}"
                phrase_counter[trigram] += 1

    # Also count simple keyword recurrence across all entries
    keyword_counter: Counter = Counter()
    for entry in entries:
        words = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_\-]{3,}\b", entry.text.lower()))
        for w in words:
            keyword_counter[w] += 1

    # Merge: report anything above threshold
    candidates = []
    seen = set()
    for phrase, count in phrase_counter.most_common(20):
        if count >= threshold and phrase not in seen:
            candidates.append((phrase, count))
            seen.add(phrase)

    return candidates[:10]  # top 10


def find_consolidation_groups(entries: List[MemoryEntry]) -> List[List[MemoryEntry]]:
    """Group semantically related entries that could be consolidated."""
    # Simple approach: group entries sharing the same category
    by_category = defaultdict(list)
    for entry in entries:
        key = entry.category or "_uncategorized"
        by_category[key].append(entry)

    # Return categories with 4+ entries (ripe for consolidation into a topic file)
    return [group for group in by_category.values() if len(group) >= 4]


def print_text_report(report: HealthReport, filter_mode: Optional[str] = None) -> None:
    print("\nClaude Code Memory Health Report")
    print("=" * 50)
    print(f"Memory directory: {report.memory_path}")

    if not report.main_file_exists:
        print("\n⚠  MEMORY.md not found — auto-memory may not be active.")
        print("   Start a Claude Code session in this project to initialize memory.")
        return

    # Utilization
    bar_len = 30
    filled = int(bar_len * report.utilization_pct / 100)
    bar = "█" * filled + "░" * (bar_len - filled)
    status = "OVER LIMIT" if report.is_over_limit else ("NEAR LIMIT" if report.is_near_limit else "OK")
    print(f"\nMain file: {report.main_file_lines}/{MEMORY_LIMIT} lines  [{bar}] {report.utilization_pct:.0f}%  {status}")

    if filter_mode != "promotions":
        # Topic files
        if report.topic_files:
            print(f"\nTopic files ({len(report.topic_files)}):")
            for tf in report.topic_files:
                try:
                    lc = sum(1 for _ in open(tf))
                except OSError:
                    lc = 0
                print(f"  {os.path.basename(tf):30s}  {lc} lines")
        else:
            print("\nNo topic files (all memory in MEMORY.md)")

        # Stale entries
        if report.stale_entries:
            print(f"\nStale entries ({len(report.stale_entries)}) — files no longer exist:")
            for e in report.stale_entries:
                print(f"  Line {e.line:3d}: {e.text[:80]}")
            print("  → Remove these to free space and reduce noise.")
        else:
            print("\nNo stale entries detected.")

        # Consolidation
        if report.consolidation_groups:
            print(f"\nConsolidation opportunities ({len(report.consolidation_groups)} category groups):")
            for group in report.consolidation_groups:
                cat = group[0].category or "uncategorized"
                print(f"  '{cat}' has {len(group)} entries — consider moving to a topic file.")

    # Promotion candidates
    if report.promotion_candidates:
        print(f"\nPromotion candidates (patterns mentioned {2}+ times):")
        print("  These recurring themes may be ready to promote to CLAUDE.md:\n")
        for phrase, count in report.promotion_candidates:
            print(f"  [{count}x]  {phrase}")
        print(f"\n  Run: /si:promote '<pattern description>' to graduate to CLAUDE.md")
    else:
        print("\nNo clear promotion candidates yet.")

    print()


def print_json_report(report: HealthReport) -> None:
    output = {
        "memory_path": report.memory_path,
        "main_file": {
            "exists": report.main_file_exists,
            "lines": report.main_file_lines,
            "limit": MEMORY_LIMIT,
            "utilization_pct": round(report.utilization_pct, 1),
            "status": "over" if report.is_over_limit else ("near" if report.is_near_limit else "ok"),
        },
        "topic_files": report.topic_files,
        "stale_entries": [
            {"line": e.line, "text": e.text, "category": e.category}
            for e in report.stale_entries
        ],
        "promotion_candidates": [
            {"phrase": p, "count": c} for p, c in report.promotion_candidates
        ],
        "consolidation_groups": [
            {
                "category": group[0].category,
                "entry_count": len(group),
                "entries": [{"line": e.line, "text": e.text} for e in group],
            }
            for group in report.consolidation_groups
        ],
    }
    print(json.dumps(output, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Claude Code auto-memory health and find promotion candidates"
    )
    parser.add_argument(
        "memory_dir",
        nargs="?",
        help="Path to memory directory (auto-detected from cwd if omitted)",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--filter",
        choices=["promotions", "stale", "all"],
        default="all",
        help="Show only specific section (default: all)",
    )
    args = parser.parse_args()

    # Resolve memory directory
    if args.memory_dir:
        memory_dir = args.memory_dir
    else:
        memory_dir = find_memory_dir(os.getcwd())
        if not memory_dir:
            # Try common locations
            home = str(Path.home())
            default = os.path.join(home, ".claude", "projects")
            print(f"Auto-detect failed. Memory dirs in {default}:", file=sys.stderr)
            if os.path.isdir(default):
                for d in sorted(os.listdir(default)):
                    mem = os.path.join(default, d, "memory")
                    if os.path.isdir(mem):
                        print(f"  {mem}", file=sys.stderr)
            print("Re-run with explicit path: python memory_health.py <path>", file=sys.stderr)
            sys.exit(1)

    main_file = os.path.join(memory_dir, "MEMORY.md")
    main_exists = os.path.isfile(main_file)
    main_lines = 0
    entries = []

    if main_exists:
        with open(main_file, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        main_lines = len(all_lines)
        entries = parse_memory_file(main_file)

    # Topic files (anything in the directory that isn't MEMORY.md)
    topic_files = []
    if os.path.isdir(memory_dir):
        for fname in sorted(os.listdir(memory_dir)):
            if fname != "MEMORY.md" and fname.endswith(".md"):
                topic_files.append(os.path.join(memory_dir, fname))

    # Determine project root (two levels up from memory dir)
    project_root = str(Path(memory_dir).parent.parent)

    stale = detect_stale_entries(entries, project_root) if entries else []
    promotions = detect_promotion_candidates(entries) if entries else []
    groups = find_consolidation_groups(entries) if entries else []

    report = HealthReport(
        memory_path=memory_dir,
        main_file_lines=main_lines,
        main_file_exists=main_exists,
        topic_files=topic_files,
        entries=entries,
        stale_entries=stale,
        promotion_candidates=promotions,
        consolidation_groups=groups,
    )

    if args.output == "json":
        print_json_report(report)
    else:
        print_text_report(report, filter_mode=args.filter)


if __name__ == "__main__":
    main()
