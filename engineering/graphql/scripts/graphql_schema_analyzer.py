#!/usr/bin/env python3
"""
graphql_schema_analyzer.py — Static analysis of GraphQL SDL files.

Usage:
    python3 graphql_schema_analyzer.py schema.graphql
    python3 graphql_schema_analyzer.py schema.graphql --output json
    python3 graphql_schema_analyzer.py schema.graphql --fix

Exit codes:
    0 — no WARNING or CRITICAL findings
    1 — one or more WARNING or CRITICAL findings
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    severity: str        # CRITICAL | WARNING | NOTE
    line: int
    rule: str
    message: str
    fix: Optional[str] = None


@dataclass
class AnalysisResult:
    file: str
    findings: List[Finding] = field(default_factory=list)

    def has_blocking(self) -> bool:
        return any(f.severity in ("CRITICAL", "WARNING") for f in self.findings)

    def counts(self):
        counts = {"CRITICAL": 0, "WARNING": 0, "NOTE": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Tokenizer / SDL parser (stdlib only — no graphql-core)
# ---------------------------------------------------------------------------

@dataclass
class TypeDef:
    kind: str           # type | input | interface | enum | union | scalar | subscription-type | query-type | mutation-type
    name: str
    line: int
    fields: List[dict] = field(default_factory=list)
    description: Optional[str] = None


def strip_comments(text: str) -> List[tuple]:
    """Return list of (line_number, line_text) with # comments removed but line numbers preserved."""
    lines = text.splitlines()
    result = []
    for i, line in enumerate(lines, start=1):
        # Remove inline # comments (not inside strings)
        clean = re.sub(r'#[^\n]*', '', line)
        result.append((i, clean))
    return result


def extract_descriptions(text: str) -> dict:
    """Return a dict mapping line_number -> description string for triple-quoted descriptions."""
    descriptions = {}
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith('"""'):
            desc_start_line = i + 1  # 1-based: description is ON this line
            parts = [stripped[3:]]
            if stripped.count('"""') >= 2 and stripped.endswith('"""') and len(stripped) > 6:
                # Single-line triple quote
                descriptions[i + 2] = stripped[3:stripped.rfind('"""')].strip()
                i += 1
                continue
            i += 1
            while i < len(lines) and '"""' not in lines[i]:
                parts.append(lines[i])
                i += 1
            if i < len(lines):
                parts.append(lines[i][:lines[i].find('"""')])
            full_desc = ' '.join(p.strip() for p in parts if p.strip())
            # Map to the NEXT non-empty line after the closing """
            next_line = i + 2  # 1-based line after closing """
            descriptions[next_line] = full_desc
        i += 1
    return descriptions


def parse_sdl(text: str) -> List[TypeDef]:
    """
    Minimal SDL parser. Extracts type/input/enum/interface/union definitions
    and their fields. Does not require graphql-core.
    """
    types: List[TypeDef] = []
    lines = text.splitlines()
    descriptions = extract_descriptions(text)

    # Pattern: optional 'extend' then kind name [implements ...] {
    type_header = re.compile(
        r'^(?:extend\s+)?(type|input|interface|enum|union|scalar)\s+(\w+)'
    )

    i = 0
    while i < len(lines):
        line_no = i + 1
        line = lines[i].strip()

        # Skip comments and empty lines
        if not line or line.startswith('#'):
            i += 1
            continue

        m = type_header.match(line)
        if m:
            kind = m.group(1)
            name = m.group(2)
            desc = descriptions.get(line_no)

            tdef = TypeDef(kind=kind, name=name, line=line_no, description=desc)

            # Determine actual kind for query/mutation/subscription roots
            if kind == 'type' and name == 'Query':
                tdef.kind = 'query-type'
            elif kind == 'type' and name == 'Mutation':
                tdef.kind = 'mutation-type'
            elif kind == 'type' and name == 'Subscription':
                tdef.kind = 'subscription-type'

            # Collect fields until closing brace
            # Find opening brace
            block = line
            brace_depth = block.count('{') - block.count('}')
            if '{' not in block:
                # Opening brace may be on next line
                i += 1
                while i < len(lines) and '{' not in lines[i]:
                    i += 1
                if i < len(lines):
                    block = lines[i]
                    brace_depth = 1
                else:
                    types.append(tdef)
                    continue

            i += 1
            while i < len(lines) and brace_depth > 0:
                fline = lines[i]
                fline_no = i + 1
                fline_stripped = re.sub(r'#[^\n]*', '', fline).strip()

                brace_depth += fline_stripped.count('{') - fline_stripped.count('}')

                if brace_depth > 0 and fline_stripped:
                    # Parse field: name(args): Type
                    field_match = re.match(
                        r'^(\w+)\s*(?:\([^)]*\))?\s*:\s*(.+?)(?:\s*@\S+.*)?$',
                        fline_stripped
                    )
                    if field_match:
                        field_name = field_match.group(1)
                        field_type = field_match.group(2).strip()
                        has_deprecated = '@deprecated' in fline
                        field_desc = descriptions.get(fline_no)

                        # Parse args from the field line
                        args_match = re.search(r'\(([^)]*)\)', fline_stripped)
                        args_text = args_match.group(1) if args_match else ''
                        arg_names = re.findall(r'(\w+)\s*:', args_text)

                        tdef.fields.append({
                            'name': field_name,
                            'type': field_type,
                            'line': fline_no,
                            'deprecated': has_deprecated,
                            'description': field_desc,
                            'args': arg_names,
                            'raw': fline_stripped,
                        })
                i += 1

            types.append(tdef)
            continue

        i += 1

    return types


# ---------------------------------------------------------------------------
# Analysis rules
# ---------------------------------------------------------------------------

PAGINATION_ARGS = {'first', 'last', 'after', 'before', 'limit', 'offset', 'page'}
LEGACY_NAME_PATTERNS = re.compile(r'(old|legacy|deprecated)', re.IGNORECASE)
LIST_TYPE_RE = re.compile(r'\[')


def is_list_type(type_str: str) -> bool:
    return '[' in type_str


def is_nullable_list_item(type_str: str) -> bool:
    """[Type] or [Type]! — items are nullable (should be [Type!]!)"""
    m = re.match(r'\[(\w+)\]', type_str.strip())
    return bool(m)


def get_inner_list_type(type_str: str) -> Optional[str]:
    m = re.match(r'\[(\w+!?)\]', type_str.strip())
    return m.group(1).rstrip('!') if m else None


def analyze(types: List[TypeDef], all_list_returning_types: set) -> List[Finding]:
    findings: List[Finding] = []

    # Track which type names return lists (for N+1 detection)
    # Pre-pass: collect object types that have list fields
    object_types_with_list_fields: dict = {}  # type_name -> [field_names]
    for tdef in types:
        if tdef.kind not in ('type', 'query-type', 'mutation-type', 'subscription-type', 'interface'):
            continue
        list_fields = [f['name'] for f in tdef.fields if is_list_type(f['type'])]
        if list_fields:
            object_types_with_list_fields[tdef.name] = list_fields

    for tdef in types:
        # --- Rule: missing description on types ---
        if tdef.kind in ('type', 'input', 'interface') and not tdef.description:
            findings.append(Finding(
                severity='NOTE',
                line=tdef.line,
                rule='missing-type-description',
                message=f'Type `{tdef.name}` has no description string.',
                fix=f'Add """\nDescription of {tdef.name}.\n""" above the type definition.',
            ))

        # --- Rule: types with >15 fields ---
        if tdef.kind in ('type', 'input', 'interface') and len(tdef.fields) > 15:
            findings.append(Finding(
                severity='NOTE',
                line=tdef.line,
                rule='too-many-fields',
                message=f'Type `{tdef.name}` has {len(tdef.fields)} fields — consider splitting into focused types.',
                fix=f'Split `{tdef.name}` into smaller types (e.g., `{tdef.name}Profile`, `{tdef.name}Settings`).',
            ))

        # --- Rule: missing id: ID! on object types (not connection/edge/pageInfo/input) ---
        if tdef.kind == 'type':
            skip_suffixes = ('Connection', 'Edge', 'PageInfo', 'Payload', 'Error')
            if not any(tdef.name.endswith(s) for s in skip_suffixes):
                has_id = any(
                    f['name'] == 'id' and 'ID' in f['type'] and '!' in f['type']
                    for f in tdef.fields
                )
                if not has_id and tdef.fields:  # skip empty types
                    findings.append(Finding(
                        severity='WARNING',
                        line=tdef.line,
                        rule='missing-id-field',
                        message=f'Type `{tdef.name}` is missing `id: ID!`.',
                        fix=f'Add `id: ID!` as the first field of `{tdef.name}`.',
                    ))

        # --- Per-field rules ---
        for f in tdef.fields:
            fname = f['name']
            ftype = f['type']
            fline = f['line']

            # --- Rule: missing description on fields in Query type ---
            if tdef.kind == 'query-type' and not f.get('description'):
                findings.append(Finding(
                    severity='NOTE',
                    line=fline,
                    rule='missing-field-description',
                    message=f'Query field `{fname}` has no description string.',
                    fix=f'Add """Description.""" above the `{fname}` field.',
                ))

            # --- Rule: nullable list items [Type] ---
            if is_nullable_list_item(ftype):
                findings.append(Finding(
                    severity='NOTE',
                    line=fline,
                    rule='nullable-list-item',
                    message=f'`{tdef.name}.{fname}` uses `{ftype}` — list items are nullable. Prefer `[{get_inner_list_type(ftype) or "Type"}!]!`.',
                    fix=f'Change `{ftype}` to `[{get_inner_list_type(ftype) or "Type"}!]!`.',
                ))

            # --- Rule: legacy field name without @deprecated ---
            if LEGACY_NAME_PATTERNS.search(fname) and not f['deprecated']:
                findings.append(Finding(
                    severity='WARNING',
                    line=fline,
                    rule='missing-deprecated-directive',
                    message=f'`{tdef.name}.{fname}` looks deprecated by name but has no `@deprecated` directive.',
                    fix=f'Add `@deprecated(reason: "Use `newFieldName` instead.")` to `{fname}`.',
                ))

            # --- Rule: query/list fields missing pagination args ---
            if tdef.kind == 'query-type' and is_list_type(ftype):
                has_pagination = bool(set(f['args']) & PAGINATION_ARGS)
                if not has_pagination:
                    findings.append(Finding(
                        severity='WARNING',
                        line=fline,
                        rule='missing-pagination-args',
                        message=f'Query `{fname}` returns a list but has no pagination args (first/after/last/before).',
                        fix=f'Add `{fname}(first: Int, after: String): {ftype}` or use a Connection type.',
                    ))

            # --- Rule: mutation without input type ---
            if tdef.kind == 'mutation-type' and f['args']:
                arg_types_in_raw = re.findall(r':\s*(\w+)', f.get('raw', ''))
                # If none of the arg types ends with 'Input', flag it
                has_input_type = any(
                    a.endswith('Input') for a in arg_types_in_raw
                )
                if not has_input_type:
                    findings.append(Finding(
                        severity='WARNING',
                        line=fline,
                        rule='mutation-without-input-type',
                        message=f'Mutation `{fname}` takes raw args instead of an input type.',
                        fix=f'Create `input {fname[0].upper()}{fname[1:]}Input {{ ... }}` and use `{fname}(input: {fname[0].upper()}{fname[1:]}Input!)`.',
                    ))

            # --- Rule: subscription without filter arg ---
            if tdef.kind == 'subscription-type' and not f['args']:
                findings.append(Finding(
                    severity='NOTE',
                    line=fline,
                    rule='subscription-without-filter',
                    message=f'Subscription `{fname}` has no filter args — will broadcast to all subscribers.',
                    fix=f'Add a filter arg: `{fname}(userId: ID!): {ftype}`.',
                ))

            # --- Rule: N+1 risk — list field on a type that itself appears in list fields ---
            if tdef.kind == 'type' and is_list_type(ftype):
                inner = get_inner_list_type(ftype)
                if inner and inner in object_types_with_list_fields:
                    findings.append(Finding(
                        severity='WARNING',
                        line=fline,
                        rule='n-plus-one-risk',
                        message=(
                            f'`{tdef.name}.{fname}` returns a list of `{inner}`, '
                            f'which itself has list fields {object_types_with_list_fields[inner]}. '
                            f'High N+1 risk if loaded without DataLoader.'
                        ),
                        fix=f'Use a DataLoader keyed on `{tdef.name.lower()}Id` to batch-load `{fname}`.',
                    ))

    return findings


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_text(result: AnalysisResult, show_fix: bool = False) -> str:
    lines = []
    counts = result.counts()

    lines.append(f'GraphQL Schema Analysis — {result.file}')
    lines.append('=' * 60)
    lines.append(
        f'CRITICAL: {counts["CRITICAL"]}  WARNING: {counts["WARNING"]}  NOTE: {counts["NOTE"]}'
    )
    lines.append('')

    if not result.findings:
        lines.append('No issues found.')
        return '\n'.join(lines)

    # Group by severity
    for severity in ('CRITICAL', 'WARNING', 'NOTE'):
        group = [f for f in result.findings if f.severity == severity]
        if not group:
            continue
        lines.append(f'--- {severity} ---')
        for finding in sorted(group, key=lambda x: x.line):
            lines.append(f'  Line {finding.line:>4}  [{finding.rule}]')
            lines.append(f'           {finding.message}')
            if show_fix and finding.fix:
                lines.append(f'           FIX: {finding.fix}')
        lines.append('')

    return '\n'.join(lines)


def format_json(result: AnalysisResult) -> str:
    counts = result.counts()
    data = {
        'file': result.file,
        'summary': counts,
        'has_blocking': result.has_blocking(),
        'findings': [
            {
                'severity': f.severity,
                'line': f.line,
                'rule': f.rule,
                'message': f.message,
                'fix': f.fix,
            }
            for f in sorted(result.findings, key=lambda x: (x.line, x.severity))
        ],
    }
    return json.dumps(data, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Analyze a GraphQL SDL file for common issues.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('schema', help='Path to the .graphql SDL file')
    parser.add_argument(
        '--output',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)',
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Include fix suggestions in text output',
    )
    args = parser.parse_args()

    try:
        with open(args.schema, 'r', encoding='utf-8') as fh:
            content = fh.read()
    except FileNotFoundError:
        print(f'Error: file not found: {args.schema}', file=sys.stderr)
        sys.exit(2)
    except IOError as e:
        print(f'Error reading file: {e}', file=sys.stderr)
        sys.exit(2)

    # Parse and analyze
    all_list_returning_types: set = set()
    types = parse_sdl(content)
    findings = analyze(types, all_list_returning_types)

    result = AnalysisResult(file=args.schema, findings=findings)

    # Output
    if args.output == 'json':
        print(format_json(result))
    else:
        print(format_text(result, show_fix=args.fix))

    # Exit code
    sys.exit(1 if result.has_blocking() else 0)


if __name__ == '__main__':
    main()
