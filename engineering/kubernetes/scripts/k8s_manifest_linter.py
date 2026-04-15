#!/usr/bin/env python3
"""
k8s_manifest_linter.py — Static analysis for Kubernetes YAML manifests.

Usage:
    python3 k8s_manifest_linter.py deployment.yaml
    python3 k8s_manifest_linter.py k8s/ --recursive
    python3 k8s_manifest_linter.py k8s/ --recursive --output json

Exit codes:
    0 — no findings, or only WARNING/NOTE findings
    1 — one or more CRITICAL findings
"""

import argparse
import json
import os
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------------------
# Severity constants
# ---------------------------------------------------------------------------
CRITICAL = "CRITICAL"
WARNING = "WARNING"
NOTE = "NOTE"

SEVERITY_ORDER = {CRITICAL: 0, WARNING: 1, NOTE: 2}


# ---------------------------------------------------------------------------
# Finding dataclass (plain dict for stdlib compatibility)
# ---------------------------------------------------------------------------
def finding(severity, code, message, path="", line=None):
    return {
        "severity": severity,
        "code": code,
        "message": message,
        "path": path,
        "line": line,
    }


# ---------------------------------------------------------------------------
# YAML loading helpers
# ---------------------------------------------------------------------------
def load_yaml_docs(filepath):
    """Load all YAML documents from a file. Returns list of (doc, error)."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            content = fh.read()
        docs = list(yaml.safe_load_all(content))
        return [d for d in docs if d is not None], None
    except yaml.YAMLError as exc:
        return [], f"YAML parse error: {exc}"
    except OSError as exc:
        return [], f"File read error: {exc}"


def collect_yaml_files(path, recursive):
    """Return list of .yaml/.yml file paths under path."""
    if os.path.isfile(path):
        return [path]
    results = []
    if recursive:
        for root, _dirs, files in os.walk(path):
            for fname in files:
                if fname.endswith((".yaml", ".yml")):
                    results.append(os.path.join(root, fname))
    else:
        for fname in os.listdir(path):
            if fname.endswith((".yaml", ".yml")):
                results.append(os.path.join(path, fname))
    return sorted(results)


# ---------------------------------------------------------------------------
# Line-number helper
# ---------------------------------------------------------------------------
def find_line(filepath, search_string):
    """Return first 1-based line number containing search_string, or None."""
    try:
        with open(filepath, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if search_string in line:
                    return i
    except OSError:
        pass
    return None


# ---------------------------------------------------------------------------
# Per-container checks
# ---------------------------------------------------------------------------
def check_container(container, filepath, findings):
    name = container.get("name", "<unnamed>")

    # CRITICAL: missing resources
    resources = container.get("resources", {})
    requests = resources.get("requests") if isinstance(resources, dict) else None
    limits = resources.get("limits") if isinstance(resources, dict) else None

    if not requests:
        ln = find_line(filepath, f"name: {name}")
        findings.append(finding(
            CRITICAL, "MISSING_REQUESTS",
            f"Container '{name}' has no resources.requests — pod may starve node or be unschedulable",
            line=ln,
        ))
    if not limits:
        ln = find_line(filepath, f"name: {name}")
        findings.append(finding(
            CRITICAL, "MISSING_LIMITS",
            f"Container '{name}' has no resources.limits — OOMKill risk and noisy-neighbour risk",
            line=ln,
        ))

    # WARNING: image:latest
    image = container.get("image", "")
    if isinstance(image, str):
        tag = image.split(":")[-1] if ":" in image else "latest"
        if tag in ("latest", "") or "@" not in image and ":" not in image:
            ln = find_line(filepath, f"image: {image}")
            findings.append(finding(
                WARNING, "MUTABLE_IMAGE_TAG",
                f"Container '{name}' uses mutable/missing image tag '{image}' — pin to digest or semver",
                line=ln,
            ))

    # WARNING: missing liveness probe
    if "livenessProbe" not in container:
        findings.append(finding(
            WARNING, "MISSING_LIVENESS_PROBE",
            f"Container '{name}' has no livenessProbe — deadlocked pods will not be restarted",
        ))

    # WARNING: missing readiness probe
    if "readinessProbe" not in container:
        findings.append(finding(
            WARNING, "MISSING_READINESS_PROBE",
            f"Container '{name}' has no readinessProbe — pod receives traffic before it is ready",
        ))

    # CRITICAL: privileged container
    sc = container.get("securityContext", {}) or {}
    if sc.get("privileged") is True:
        ln = find_line(filepath, "privileged: true")
        findings.append(finding(
            CRITICAL, "PRIVILEGED_CONTAINER",
            f"Container '{name}' runs as privileged — equivalent to root on the host node",
            line=ln,
        ))

    # WARNING: missing runAsNonRoot
    if not sc.get("runAsNonRoot") and not sc.get("runAsUser"):
        findings.append(finding(
            WARNING, "NO_RUN_AS_NON_ROOT",
            f"Container '{name}' does not set securityContext.runAsNonRoot or runAsUser — may run as root",
        ))

    # NOTE: imagePullPolicy missing when tag is mutable
    pull_policy = container.get("imagePullPolicy")
    if pull_policy != "Always" and isinstance(image, str):
        tag = image.split(":")[-1] if ":" in image else "latest"
        if tag in ("latest", ""):
            findings.append(finding(
                NOTE, "MISSING_IMAGE_PULL_POLICY",
                f"Container '{name}' uses mutable tag but imagePullPolicy is not 'Always' — stale image may be used",
            ))


# ---------------------------------------------------------------------------
# Per-document checks
# ---------------------------------------------------------------------------
def check_document(doc, filepath, findings):
    kind = doc.get("kind", "")
    metadata = doc.get("metadata", {}) or {}

    # NOTE: missing namespace
    if not metadata.get("namespace"):
        findings.append(finding(
            NOTE, "MISSING_NAMESPACE",
            f"Resource '{metadata.get('name', '<unnamed>')}' ({kind}) has no namespace — will deploy to current context namespace",
        ))

    if kind in ("Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job", "CronJob"):
        _check_workload(doc, kind, filepath, findings)


def _check_workload(doc, kind, filepath, findings):
    metadata = doc.get("metadata", {}) or {}
    spec = doc.get("spec", {}) or {}
    name = metadata.get("name", "<unnamed>")

    # NOTE: replicas: 1 on Deployment
    replicas = spec.get("replicas", 1)
    if kind == "Deployment" and replicas == 1:
        ln = find_line(filepath, "replicas: 1")
        findings.append(finding(
            NOTE, "SINGLE_REPLICA",
            f"Deployment '{name}' has replicas=1 — single point of failure; node drain will cause downtime",
            line=ln,
        ))

    # Drill into pod template
    if kind == "CronJob":
        job_spec = spec.get("jobTemplate", {}).get("spec", {}) or {}
        pod_template = job_spec.get("template", {}) or {}
    else:
        pod_template = spec.get("template", {}) or {}

    pod_spec = pod_template.get("spec", {}) or {}
    pod_meta = pod_template.get("metadata", {}) or {}

    # CRITICAL: hostNetwork
    if pod_spec.get("hostNetwork") is True:
        ln = find_line(filepath, "hostNetwork: true")
        findings.append(finding(
            CRITICAL, "HOST_NETWORK",
            f"Workload '{name}' uses hostNetwork:true — bypasses network isolation, exposes host interfaces",
            line=ln,
        ))

    # CRITICAL: hostPID
    if pod_spec.get("hostPID") is True:
        ln = find_line(filepath, "hostPID: true")
        findings.append(finding(
            CRITICAL, "HOST_PID",
            f"Workload '{name}' uses hostPID:true — allows container to see all host processes",
            line=ln,
        ))

    # NOTE: missing podAntiAffinity when replicas > 1
    if kind == "Deployment" and replicas > 1:
        affinity = pod_spec.get("affinity", {}) or {}
        if not affinity.get("podAntiAffinity"):
            findings.append(finding(
                NOTE, "MISSING_POD_ANTI_AFFINITY",
                f"Deployment '{name}' has replicas={replicas} but no podAntiAffinity — all pods may land on same node",
            ))

    # Per-container checks
    containers = pod_spec.get("containers", []) or []
    init_containers = pod_spec.get("initContainers", []) or []

    for container in containers + init_containers:
        if isinstance(container, dict):
            check_container(container, filepath, findings)


# ---------------------------------------------------------------------------
# Main lint function
# ---------------------------------------------------------------------------
def lint_file(filepath):
    """Return list of findings for a single file."""
    docs, error = load_yaml_docs(filepath)
    findings = []

    if error:
        findings.append(finding(
            CRITICAL, "PARSE_ERROR",
            f"Failed to parse YAML: {error}",
        ))
        return findings

    for doc in docs:
        if not isinstance(doc, dict):
            continue
        check_document(doc, filepath, findings)

    # Attach filepath to all findings
    for f in findings:
        f["path"] = filepath

    return findings


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------
def format_text(results):
    """results: list of {file, findings}"""
    lines = []
    total_critical = 0
    total_warning = 0
    total_note = 0

    for entry in results:
        filepath = entry["file"]
        file_findings = sorted(entry["findings"], key=lambda x: SEVERITY_ORDER.get(x["severity"], 99))

        if not file_findings:
            lines.append(f"\n[OK] {filepath}")
            continue

        c = sum(1 for f in file_findings if f["severity"] == CRITICAL)
        w = sum(1 for f in file_findings if f["severity"] == WARNING)
        n = sum(1 for f in file_findings if f["severity"] == NOTE)
        total_critical += c
        total_warning += w
        total_note += n

        header = f"\n{filepath}  [{c} CRITICAL | {w} WARNING | {n} NOTE]"
        lines.append(header)
        lines.append("-" * len(header.strip()))

        for f in file_findings:
            loc = f" (line {f['line']})" if f.get("line") else ""
            lines.append(f"  [{f['severity']:8s}] {f['code']}{loc}")
            lines.append(f"             {f['message']}")

    lines.append("")
    lines.append("=" * 60)
    lines.append(f"SUMMARY  CRITICAL:{total_critical}  WARNING:{total_warning}  NOTE:{total_note}")
    lines.append("=" * 60)

    return "\n".join(lines)


def format_json(results):
    return json.dumps(results, indent=2)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Lint Kubernetes YAML manifests for common issues.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 k8s_manifest_linter.py deployment.yaml
  python3 k8s_manifest_linter.py k8s/ --recursive
  python3 k8s_manifest_linter.py k8s/ --recursive --output json
""",
    )
    parser.add_argument("path", help="Path to a YAML file or directory")
    parser.add_argument("--recursive", "-r", action="store_true", help="Recurse into subdirectories")
    parser.add_argument(
        "--output",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.path):
        print(f"ERROR: Path does not exist: {args.path}", file=sys.stderr)
        sys.exit(2)

    files = collect_yaml_files(args.path, args.recursive)
    if not files:
        print("No YAML files found.", file=sys.stderr)
        sys.exit(0)

    results = []
    has_critical = False

    for filepath in files:
        file_findings = lint_file(filepath)
        results.append({"file": filepath, "findings": file_findings})
        if any(f["severity"] == CRITICAL for f in file_findings):
            has_critical = True

    if args.output == "json":
        print(format_json(results))
    else:
        print(format_text(results))

    sys.exit(1 if has_critical else 0)


if __name__ == "__main__":
    main()
