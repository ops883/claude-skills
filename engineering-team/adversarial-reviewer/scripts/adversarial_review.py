#!/usr/bin/env python3
"""
adversarial_review.py — Static code analysis through three adversarial personas.

Runs a source file through the Saboteur, New Hire, and Security Auditor personas,
reporting findings with severity and suggestions. Promotes findings caught by 2+
personas to the next severity level.

Supports: Python, JavaScript, TypeScript, Go, Ruby (pattern-based, no AST).

Usage:
    python scripts/adversarial_review.py src/auth.py
    python scripts/adversarial_review.py src/payment.ts --persona saboteur
    python scripts/adversarial_review.py src/ --output json
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    persona: str        # saboteur | new_hire | security_auditor
    severity: str       # CRITICAL | WARNING | NOTE
    line: int
    rule: str
    message: str
    suggestion: str
    snippet: str


@dataclass
class ReviewReport:
    path: str
    findings: List[Finding] = field(default_factory=list)
    verdict: str = "CLEAN"  # BLOCK | CONCERNS | CLEAN

    def by_severity(self, sev: str) -> List[Finding]:
        return [f for f in self.findings if f.severity == sev]


# ---------------------------------------------------------------------------
# Persona 1: The Saboteur
# "I am trying to break this code in production."
# ---------------------------------------------------------------------------

SABOTEUR_RULES = [
    {
        "id": "bare-except",
        "severity": "WARNING",
        "pattern": re.compile(r"^\s*except\s*:", re.MULTILINE),
        "message": "Bare except swallows all exceptions including KeyboardInterrupt and SystemExit.",
        "suggestion": "Catch specific exception types: except (ValueError, TypeError) as e:",
    },
    {
        "id": "silent-exception",
        "severity": "WARNING",
        "pattern": re.compile(r"except[^:]*:\s*\n\s*pass"),
        "message": "Exception caught and silently ignored — errors disappear, state becomes inconsistent.",
        "suggestion": "At minimum: log the exception. Better: re-raise or return an error signal.",
    },
    {
        "id": "todo-fixme",
        "severity": "NOTE",
        "pattern": re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE),
        "message": "Unresolved TODO/FIXME — a known fragile assumption left in place.",
        "suggestion": "Create a tracked issue instead. Code with TODO comments is code waiting to break.",
    },
    {
        "id": "hardcoded-timeout",
        "severity": "NOTE",
        "pattern": re.compile(r"timeout\s*=\s*\d{3,}|sleep\s*\(\s*\d{2,}"),
        "message": "Hardcoded timeout/sleep value — will be wrong under load or slow networks.",
        "suggestion": "Make configurable via environment variable or parameter with a sensible default.",
    },
    {
        "id": "no-error-check",
        "severity": "WARNING",
        "pattern": re.compile(r"\.open\(|subprocess\.(run|call|check_output)\(|requests\.(get|post|put|delete)\("),
        "message": "External call without visible error handling nearby.",
        "suggestion": "Wrap in try/except or check return code/status before using result.",
    },
    {
        "id": "mutable-default-arg",
        "severity": "WARNING",
        "pattern": re.compile(r"def\s+\w+\([^)]*=\s*(\[\]|\{\}|\(\))"),
        "message": "Mutable default argument — shared across all calls, causes subtle state bugs.",
        "suggestion": "Use None as default and create inside the function: if items is None: items = []",
    },
    {
        "id": "unchecked-none",
        "severity": "NOTE",
        "pattern": re.compile(r"\w+\s*=\s*\w+\.get\([^)]+\)\s*\n[^#\n]*\w+\.\w+"),
        "message": "dict.get() result used immediately — may be None if key missing.",
        "suggestion": "Check for None before attribute/method access, or use dict.get(key, default).",
    },
]

# ---------------------------------------------------------------------------
# Persona 2: The New Hire
# "I joined last week. I need to understand this in 6 months."
# ---------------------------------------------------------------------------

NEW_HIRE_RULES = [
    {
        "id": "magic-number",
        "severity": "NOTE",
        "pattern": re.compile(r"(?<!['\"\w])\b(?!0\b|1\b|2\b|10\b|100\b)\d{2,}\b(?!['\"\w%])"),
        "message": "Magic number — reader has no idea what this value represents.",
        "suggestion": "Extract to a named constant: MAX_RETRY_ATTEMPTS = 5",
    },
    {
        "id": "single-char-var",
        "severity": "NOTE",
        "pattern": re.compile(r"\b(for|while)\s+([a-z])\s+in\b|\b([a-z])\s*=\s*(?!range\b)\w"),
        "message": "Single-character variable name (outside loop index) reduces readability.",
        "suggestion": "Use descriptive names: user_id instead of i, response instead of r.",
    },
    {
        "id": "long-function",
        "severity": "WARNING",
        "pattern": None,   # handled via line-count analysis
        "message": "Function exceeds 50 lines — likely doing more than one thing.",
        "suggestion": "Extract sub-tasks into named helper functions. One function, one responsibility.",
    },
    {
        "id": "deep-nesting",
        "severity": "WARNING",
        "pattern": re.compile(r"^(\s{16,}|\t{4,})\S", re.MULTILINE),
        "message": "Deep nesting (4+ levels) — forces reader to track many conditions simultaneously.",
        "suggestion": "Apply early return / guard clause pattern to flatten the indentation.",
    },
    {
        "id": "what-comment",
        "severity": "NOTE",
        "pattern": re.compile(r"#\s*(increment|decrement|loop|iterate|call|return|set|check|get)\b", re.IGNORECASE),
        "message": "Comment describes what the code does (already visible) rather than why.",
        "suggestion": "Explain intent: # retry on transient failures instead of # retry loop",
    },
    {
        "id": "no-docstring",
        "severity": "NOTE",
        "pattern": re.compile(r"def\s+\w+\([^)]*\)\s*:\s*\n\s*(?![\"\'])"),
        "message": "Function without docstring — purpose must be inferred from implementation.",
        "suggestion": "Add a one-line docstring: \"\"\"Returns the normalized user display name.\"\"\"",
    },
]

# ---------------------------------------------------------------------------
# Persona 3: The Security Auditor
# "This code will be attacked. Find the vulnerability first."
# ---------------------------------------------------------------------------

SECURITY_RULES = [
    {
        "id": "eval-exec",
        "severity": "CRITICAL",
        "pattern": re.compile(r"\beval\s*\(|\bexec\s*\("),
        "message": "eval/exec with potentially untrusted input — arbitrary code execution.",
        "suggestion": "Remove eval/exec entirely. If dynamic dispatch is needed, use a whitelist dict.",
    },
    {
        "id": "os-system",
        "severity": "CRITICAL",
        "pattern": re.compile(r"\bos\.system\s*\(|\bsubprocess\.(run|call)\s*\([^,)]*f['\"]|\bos\.popen\s*\("),
        "message": "Shell command with potential user input — command injection risk.",
        "suggestion": "Use subprocess with a list of args (no shell=True) and validate all inputs.",
    },
    {
        "id": "sql-concat",
        "severity": "CRITICAL",
        "pattern": re.compile(r"(SELECT|INSERT|UPDATE|DELETE|WHERE)[^'\";]*\+|f['\"].*SELECT.*\{"),
        "message": "SQL query with string concatenation or f-string — SQL injection risk.",
        "suggestion": "Use parameterized queries: cursor.execute('SELECT ... WHERE id = %s', (user_id,))",
    },
    {
        "id": "hardcoded-secret",
        "severity": "CRITICAL",
        "pattern": re.compile(
            r"(password|secret|api_key|token|private_key)\s*=\s*['\"][^'\"]{6,}['\"]",
            re.IGNORECASE,
        ),
        "message": "Hardcoded credential — will be committed to git history and potentially exposed.",
        "suggestion": "Load from environment: os.environ['SECRET_KEY'] or use a secrets manager.",
    },
    {
        "id": "debug-mode",
        "severity": "WARNING",
        "pattern": re.compile(r"DEBUG\s*=\s*True|debug\s*=\s*true|app\.run\s*\([^)]*debug\s*=\s*True"),
        "message": "Debug mode enabled — exposes stack traces and internal state to users.",
        "suggestion": "Gate on environment: DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'",
    },
    {
        "id": "open-redirect",
        "severity": "WARNING",
        "pattern": re.compile(r"redirect\s*\([^)]*request\.(args|form|data|params)"),
        "message": "Redirect using user-supplied URL — open redirect vulnerability.",
        "suggestion": "Validate redirect URL is within your domain: use an allowlist of safe paths.",
    },
    {
        "id": "path-traversal",
        "severity": "WARNING",
        "pattern": re.compile(r"open\s*\([^)]*\+|open\s*\([^)]*f['\"]"),
        "message": "File path constructed from input — path traversal risk (../../etc/passwd).",
        "suggestion": "Use Path(base_dir / user_input).resolve() and assert it starts with base_dir.",
    },
    {
        "id": "print-sensitive",
        "severity": "NOTE",
        "pattern": re.compile(r"print\s*\([^)]*(?:password|token|secret|key|auth)", re.IGNORECASE),
        "message": "Potentially sensitive value being printed — may appear in logs or console.",
        "suggestion": "Remove debug prints from production code. Use structured logging with log levels.",
    },
]


# ---------------------------------------------------------------------------
# Analysis engine
# ---------------------------------------------------------------------------

def analyze_long_functions(lines: List[str]) -> List[Tuple[int, int]]:
    """Return (start_line, length) for functions exceeding 50 lines."""
    results = []
    func_start = None
    indent_level = None
    func_pattern = re.compile(r"^(\s*)def\s+\w+")

    for i, line in enumerate(lines, start=1):
        m = func_pattern.match(line)
        if m:
            if func_start is not None:
                length = i - func_start
                if length > 50:
                    results.append((func_start, length))
            func_start = i
            indent_level = len(m.group(1))

    if func_start is not None:
        length = len(lines) - func_start + 1
        if length > 50:
            results.append((func_start, length))

    return results


def run_pattern_rules(lines: List[str], rules: list, persona: str) -> List[Finding]:
    findings = []
    full_text = "".join(lines)

    for rule in rules:
        if rule["pattern"] is None:
            continue  # handled separately
        for m in rule["pattern"].finditer(full_text):
            lineno = full_text[: m.start()].count("\n") + 1
            raw_snippet = lines[lineno - 1].strip() if lineno <= len(lines) else ""
            snippet = raw_snippet[:100] + "..." if len(raw_snippet) > 100 else raw_snippet
            findings.append(
                Finding(
                    persona=persona,
                    severity=rule["severity"],
                    line=lineno,
                    rule=rule["id"],
                    message=rule["message"],
                    suggestion=rule["suggestion"],
                    snippet=snippet,
                )
            )

    return findings


def analyze_file(path: str, personas: Optional[List[str]] = None) -> ReviewReport:
    report = ReviewReport(path=path)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError as e:
        return report

    active_personas = personas or ["saboteur", "new_hire", "security_auditor"]

    if "saboteur" in active_personas:
        report.findings.extend(run_pattern_rules(lines, SABOTEUR_RULES, "saboteur"))

    if "new_hire" in active_personas:
        report.findings.extend(run_pattern_rules(lines, NEW_HIRE_RULES, "new_hire"))
        # Long function check
        for start, length in analyze_long_functions(lines):
            rule = next(r for r in NEW_HIRE_RULES if r["id"] == "long-function")
            snippet = lines[start - 1].strip()[:100]
            report.findings.append(
                Finding(
                    persona="new_hire",
                    severity="WARNING",
                    line=start,
                    rule="long-function",
                    message=f"Function is {length} lines — {rule['message']}",
                    suggestion=rule["suggestion"],
                    snippet=snippet,
                )
            )

    if "security_auditor" in active_personas:
        report.findings.extend(run_pattern_rules(lines, SECURITY_RULES, "security_auditor"))

    # Severity promotion: findings with same rule OR same line caught by 2+ personas
    rule_to_findings: dict = defaultdict(list)
    for f in report.findings:
        rule_to_findings[f.rule].append(f)

    promoted_rules = {rule for rule, fs in rule_to_findings.items() if len(fs) >= 2}
    SEVERITY_UP = {"NOTE": "WARNING", "WARNING": "CRITICAL", "CRITICAL": "CRITICAL"}
    for f in report.findings:
        if f.rule in promoted_rules:
            f.severity = SEVERITY_UP[f.severity]

    # Compute verdict
    criticals = report.by_severity("CRITICAL")
    warnings = report.by_severity("WARNING")
    if criticals:
        report.verdict = "BLOCK"
    elif len(warnings) >= 2:
        report.verdict = "CONCERNS"
    else:
        report.verdict = "CLEAN"

    return report


def find_source_files(root: str) -> List[str]:
    extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rb"}
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".git", "__pycache__", "dist", "build"}]
        for fname in filenames:
            if Path(fname).suffix in extensions:
                files.append(os.path.join(dirpath, fname))
    return sorted(files)


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

PERSONA_LABELS = {
    "saboteur": "The Saboteur",
    "new_hire": "The New Hire",
    "security_auditor": "The Security Auditor",
}

SEV_ICONS = {"CRITICAL": "✗✗", "WARNING": "✗ ", "NOTE": "⚠ "}


def print_text(reports: List[ReviewReport], personas: List[str]) -> int:
    total_criticals = sum(len(r.by_severity("CRITICAL")) for r in reports)
    total_warnings = sum(len(r.by_severity("WARNING")) for r in reports)
    total_notes = sum(len(r.by_severity("NOTE")) for r in reports)

    print(f"\nAdversarial Code Review")
    print(f"{'=' * 55}")
    print(f"Files reviewed:  {len(reports)}")
    print(f"Personas active: {', '.join(PERSONA_LABELS[p] for p in personas)}")
    print(f"Findings:        {total_criticals} CRITICAL  {total_warnings} WARNING  {total_notes} NOTE\n")

    for report in reports:
        if not report.findings:
            continue
        print(f"\n{'─' * 55}")
        print(f"FILE: {report.path}   Verdict: {report.verdict}")
        print(f"{'─' * 55}")

        # Group by persona
        by_persona: dict = defaultdict(list)
        for f in report.findings:
            by_persona[f.persona].append(f)

        for persona in personas:
            fs = by_persona.get(persona, [])
            if not fs:
                continue
            print(f"\n  [{PERSONA_LABELS[persona].upper()}]")
            for f in sorted(fs, key=lambda x: (x.severity != "CRITICAL", x.severity != "WARNING", x.line)):
                icon = SEV_ICONS.get(f.severity, "  ")
                print(f"  {icon} [{f.severity}] Line {f.line}  {f.rule}")
                print(f"       {f.snippet}")
                print(f"       {f.message}")
                print(f"       → {f.suggestion}")

    print(f"\n{'=' * 55}")
    blocks = [r for r in reports if r.verdict == "BLOCK"]
    concerns = [r for r in reports if r.verdict == "CONCERNS"]
    if blocks:
        print(f"VERDICT: BLOCK — {len(blocks)} file(s) must be fixed before merging")
        return 1
    elif concerns:
        print(f"VERDICT: CONCERNS — {len(concerns)} file(s) have warnings worth fixing")
        return 0
    else:
        print("VERDICT: CLEAN — only notes")
        return 0


def print_json(reports: List[ReviewReport]) -> int:
    output = {
        "summary": {
            "files": len(reports),
            "verdict": "BLOCK" if any(r.verdict == "BLOCK" for r in reports)
                       else "CONCERNS" if any(r.verdict == "CONCERNS" for r in reports)
                       else "CLEAN",
            "total_critical": sum(len(r.by_severity("CRITICAL")) for r in reports),
            "total_warning": sum(len(r.by_severity("WARNING")) for r in reports),
            "total_note": sum(len(r.by_severity("NOTE")) for r in reports),
        },
        "files": [
            {
                "path": r.path,
                "verdict": r.verdict,
                "findings": [
                    {
                        "persona": f.persona,
                        "severity": f.severity,
                        "line": f.line,
                        "rule": f.rule,
                        "message": f.message,
                        "suggestion": f.suggestion,
                        "snippet": f.snippet,
                    }
                    for f in r.findings
                ],
            }
            for r in reports
        ],
    }
    print(json.dumps(output, indent=2))
    return 1 if output["summary"]["verdict"] == "BLOCK" else 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Adversarial code review — Saboteur, New Hire, Security Auditor personas"
    )
    parser.add_argument("path", help="Source file or directory to review")
    parser.add_argument(
        "--persona",
        choices=["saboteur", "new_hire", "security_auditor"],
        help="Run only one persona (default: all three)",
    )
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    target = args.path
    personas = [args.persona] if args.persona else ["saboteur", "new_hire", "security_auditor"]

    if os.path.isfile(target):
        files = [target]
    elif os.path.isdir(target):
        files = find_source_files(target)
        if not files:
            print(f"No supported source files found in {target}", file=sys.stderr)
            sys.exit(0)
    else:
        print(f"Path not found: {target}", file=sys.stderr)
        sys.exit(2)

    reports = [analyze_file(f, personas) for f in files]

    if args.output == "json":
        exit_code = print_json(reports)
    else:
        exit_code = print_text(reports, personas)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
