#!/usr/bin/env python3
"""
pw_test_analyzer.py — Playwright test anti-pattern detector.

Analyzes .spec.ts / .spec.js files against the 10 Golden Rules and reports
violations with line numbers and suggested fixes.

Usage:
    python scripts/pw_test_analyzer.py tests/auth/login.spec.ts
    python scripts/pw_test_analyzer.py tests/
    python scripts/pw_test_analyzer.py tests/ --output json
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Violation:
    rule: str
    severity: str  # "error" | "warning"
    line: int
    column: int
    message: str
    suggestion: str
    snippet: str


@dataclass
class FileReport:
    path: str
    violations: List[Violation] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for v in self.violations if v.severity == "warning")


RULES = [
    {
        "id": "no-wait-for-timeout",
        "severity": "error",
        "pattern": re.compile(r"waitForTimeout\s*\("),
        "message": "page.waitForTimeout() introduces brittle timing — tests fail randomly under load.",
        "suggestion": "Replace with a web-first assertion: await expect(locator).toBeVisible()",
    },
    {
        "id": "no-hardcoded-urls",
        "severity": "error",
        "pattern": re.compile(r"""page\.goto\s*\(\s*['"`]https?://"""),
        "message": "Hardcoded URL — breaks across environments.",
        "suggestion": "Use baseURL from playwright.config.ts: await page.goto('/path')",
    },
    {
        "id": "no-textcontent-in-expect",
        "severity": "error",
        "pattern": re.compile(r"expect\s*\(\s*await\s+.*\.textContent\(\)"),
        "message": "expect(await locator.textContent()) does not auto-retry — flaky under async renders.",
        "suggestion": "Use expect(locator).toHaveText('...') which retries automatically.",
    },
    {
        "id": "no-innertext-in-expect",
        "severity": "warning",
        "pattern": re.compile(r"expect\s*\(\s*await\s+.*\.innerText\(\)"),
        "message": "expect(await locator.innerText()) does not auto-retry.",
        "suggestion": "Use expect(locator).toHaveText('...') instead.",
    },
    {
        "id": "prefer-role-over-css",
        "severity": "warning",
        "pattern": re.compile(r"page\.locator\s*\(\s*['\"`][.#][^'\"`;]+['\"`]\s*\)"),
        "message": "CSS locator — brittle to markup changes.",
        "suggestion": "Prefer page.getByRole(), getByLabel(), getByText(), or getByTestId().",
    },
    {
        "id": "prefer-role-over-xpath",
        "severity": "error",
        "pattern": re.compile(r"page\.locator\s*\(\s*['\"`]//"),
        "message": "XPath locator — tightly coupled to DOM structure.",
        "suggestion": "Use semantic locators: getByRole(), getByLabel(), getByText().",
    },
    {
        "id": "no-sleep",
        "severity": "error",
        "pattern": re.compile(r"\bsleep\s*\(|\bsetTimeout\s*\(\s*(?:resolve|cb|\(\))", re.IGNORECASE),
        "message": "Manual sleep / setTimeout — introduces arbitrary delays.",
        "suggestion": "Wait for a specific condition: await expect(locator).toBeVisible()",
    },
    {
        "id": "no-page-pause",
        "severity": "warning",
        "pattern": re.compile(r"page\.pause\s*\("),
        "message": "page.pause() left in test — blocks CI.",
        "suggestion": "Remove page.pause(). Use --debug flag during local development instead.",
    },
    {
        "id": "no-focused-test",
        "severity": "error",
        "pattern": re.compile(r"\btest\.only\s*\(|\bit\.only\s*\(|\bdescribe\.only\s*\("),
        "message": "test.only / describe.only committed — skips the rest of the suite in CI.",
        "suggestion": "Remove .only before committing.",
    },
    {
        "id": "no-skipped-test",
        "severity": "warning",
        "pattern": re.compile(r"\btest\.skip\s*\(|\bit\.skip\s*\("),
        "message": "Skipped test — hidden coverage gap.",
        "suggestion": "Fix the underlying issue or delete the test. Skipped tests accumulate silently.",
    },
]


def analyze_file(path: str) -> FileReport:
    report = FileReport(path=path)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError as e:
        return report

    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")
        for rule in RULES:
            m = rule["pattern"].search(line)
            if m:
                col = m.start() + 1
                snippet = line.strip()
                if len(snippet) > 100:
                    snippet = snippet[:97] + "..."
                report.violations.append(
                    Violation(
                        rule=rule["id"],
                        severity=rule["severity"],
                        line=lineno,
                        column=col,
                        message=rule["message"],
                        suggestion=rule["suggestion"],
                        snippet=snippet,
                    )
                )
    return report


def find_test_files(root: str) -> List[str]:
    test_files = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            if re.search(r"\.spec\.(ts|js|tsx|jsx)$", fname):
                test_files.append(os.path.join(dirpath, fname))
    return sorted(test_files)


def print_text_report(reports: List[FileReport]) -> int:
    total_errors = sum(r.error_count for r in reports)
    total_warnings = sum(r.warning_count for r in reports)
    files_with_issues = [r for r in reports if r.violations]

    print(f"\nPlaywright Anti-Pattern Analysis")
    print(f"{'=' * 50}")
    print(f"Files scanned: {len(reports)}")
    print(f"Issues found:  {total_errors} errors, {total_warnings} warnings\n")

    if not files_with_issues:
        print("No violations found.")
        return 0

    for report in files_with_issues:
        rel = report.path
        print(f"\n{rel}")
        print(f"  {report.error_count} error(s), {report.warning_count} warning(s)")
        for v in report.violations:
            icon = "✗" if v.severity == "error" else "⚠"
            print(f"  {icon} Line {v.line}:{v.column}  [{v.rule}]")
            print(f"      {v.snippet}")
            print(f"      {v.message}")
            print(f"      → {v.suggestion}")

    print(f"\n{'=' * 50}")
    print(f"Summary: {total_errors} errors, {total_warnings} warnings across {len(files_with_issues)} file(s)")

    if total_errors > 0:
        print("Status: FAIL (errors must be fixed before merging)")
        return 1
    else:
        print("Status: PASS (warnings are advisory)")
        return 0


def print_json_report(reports: List[FileReport]) -> int:
    total_errors = sum(r.error_count for r in reports)
    output = {
        "summary": {
            "files_scanned": len(reports),
            "total_errors": total_errors,
            "total_warnings": sum(r.warning_count for r in reports),
            "files_with_issues": sum(1 for r in reports if r.violations),
        },
        "files": [
            {
                "path": r.path,
                "errors": r.error_count,
                "warnings": r.warning_count,
                "violations": [
                    {
                        "rule": v.rule,
                        "severity": v.severity,
                        "line": v.line,
                        "column": v.column,
                        "message": v.message,
                        "suggestion": v.suggestion,
                        "snippet": v.snippet,
                    }
                    for v in r.violations
                ],
            }
            for r in reports
            if r.violations
        ],
    }
    print(json.dumps(output, indent=2))
    return 1 if total_errors > 0 else 0


def main():
    parser = argparse.ArgumentParser(
        description="Analyze Playwright test files for anti-patterns"
    )
    parser.add_argument(
        "path",
        help="Test file (.spec.ts) or directory to scan",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    target = args.path
    if os.path.isfile(target):
        files = [target]
    elif os.path.isdir(target):
        files = find_test_files(target)
        if not files:
            print(f"No .spec.ts/.spec.js files found in {target}", file=sys.stderr)
            sys.exit(0)
    else:
        print(f"Path not found: {target}", file=sys.stderr)
        sys.exit(2)

    reports = [analyze_file(f) for f in files]

    if args.output == "json":
        exit_code = print_json_report(reports)
    else:
        exit_code = print_text_report(reports)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
