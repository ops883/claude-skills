#!/usr/bin/env python3
"""
stripe_webhook_validator.py — Stripe webhook handler static analyzer + scaffold generator.

Two modes:
  1. validate  — Analyze an existing webhook handler for common mistakes
  2. scaffold  — Generate a production-grade webhook handler from a list of event types

Supports Python (Flask/FastAPI) and TypeScript/JavaScript (Next.js/Express) handlers.

Usage:
    # Validate an existing handler
    python scripts/stripe_webhook_validator.py validate src/webhooks/stripe.py
    python scripts/stripe_webhook_validator.py validate app/api/webhooks/route.ts

    # Generate a scaffold
    python scripts/stripe_webhook_validator.py scaffold --lang python --events customer.subscription.created,invoice.payment_succeeded,invoice.payment_failed
    python scripts/stripe_webhook_validator.py scaffold --lang typescript --events customer.subscription.updated,customer.subscription.deleted --output src/webhooks/stripe.ts

    # List supported event types
    python scripts/stripe_webhook_validator.py events
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional


# ---------------------------------------------------------------------------
# Known event types with descriptions
# ---------------------------------------------------------------------------

STRIPE_EVENTS = {
    # Subscriptions
    "customer.subscription.created": "New subscription started",
    "customer.subscription.updated": "Plan change, trial end, status change",
    "customer.subscription.deleted": "Subscription cancelled",
    "customer.subscription.trial_will_end": "Trial ending in 3 days — send upgrade nudge",
    # Invoices
    "invoice.paid": "Successful renewal payment",
    "invoice.payment_succeeded": "Payment succeeded (alias for invoice.paid)",
    "invoice.payment_failed": "Payment failed — retry or notify customer",
    "invoice.upcoming": "Invoice will be created in 7 days",
    # Payment intents
    "payment_intent.succeeded": "One-time payment completed",
    "payment_intent.payment_failed": "One-time payment failed",
    # Checkout
    "checkout.session.completed": "Checkout finished — provision access",
    "checkout.session.expired": "Checkout abandoned",
    # Customer
    "customer.created": "New Stripe customer",
    "customer.updated": "Customer metadata/email changed",
    "customer.deleted": "Customer deleted",
    # Payment methods
    "customer.updated": "Card expiry update",
    "payment_method.attached": "Card added to customer",
    "payment_method.detached": "Card removed",
    # Disputes
    "charge.dispute.created": "Chargeback filed — respond within deadline",
    "charge.dispute.closed": "Dispute resolved",
    # Refunds
    "charge.refunded": "Refund issued",
}

CRITICAL_EVENTS = {
    "invoice.payment_failed",
    "customer.subscription.deleted",
    "charge.dispute.created",
    "checkout.session.completed",
    "customer.subscription.updated",
}


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    severity: str   # CRITICAL | WARNING | NOTE
    rule: str
    line: int
    message: str
    fix: str


@dataclass
class ValidationReport:
    path: str
    lang: str
    issues: List[Issue] = field(default_factory=list)

    def by_severity(self, sev: str) -> List[Issue]:
        return [i for i in self.issues if i.severity == sev]

    @property
    def verdict(self) -> str:
        if self.by_severity("CRITICAL"):
            return "BLOCK"
        if len(self.by_severity("WARNING")) >= 2:
            return "CONCERNS"
        return "CLEAN"


VALIDATION_RULES = [
    {
        "id": "missing-signature-verification",
        "severity": "CRITICAL",
        "python_absent": re.compile(r"stripe\.Webhook\.construct_event|webhooks\.construct_event"),
        "ts_absent": re.compile(r"stripe\.webhooks\.constructEvent|constructWebhookEvent"),
        "message": "No Stripe signature verification found.",
        "fix": "Call stripe.webhooks.constructEvent(payload, sig, process.env.STRIPE_WEBHOOK_SECRET) "
               "and catch StripeSignatureVerificationError.",
    },
    {
        "id": "missing-event-type-routing",
        "severity": "WARNING",
        "pattern": re.compile(r"event\.type|event\[.type.\]"),
        "absent": True,
        "message": "No event.type routing found — all events handled identically.",
        "fix": "Route on event.type with a switch/if-else. Unhandled types should return 200 (ignore).",
    },
    {
        "id": "missing-idempotency-check",
        "severity": "WARNING",
        "pattern": re.compile(r"event\.id|event\[.id.\]"),
        "absent": True,
        "message": "No idempotency check on event.id — duplicate events will double-process.",
        "fix": "Store processed event IDs (Redis SET or DB unique constraint). "
               "Return 200 immediately if event.id already processed.",
    },
    {
        "id": "raw-body-risk",
        "severity": "CRITICAL",
        "pattern": re.compile(r"request\.json\(\)|req\.body(?!\s*,)|\bexpress\.json"),
        "message": "JSON-parsed body used for webhook — signature verification requires raw bytes.",
        "fix": "Read raw bytes before JSON parsing: body = await request.body() (FastAPI) or "
               "use express.raw({type: 'application/json'}) in Express.",
    },
    {
        "id": "early-200-missing",
        "severity": "WARNING",
        "pattern": re.compile(r"return.*200|status.*200|\.ok\b"),
        "absent": True,
        "message": "No explicit 200 response found — Stripe retries if no 2xx returned within 30s.",
        "fix": "Always return HTTP 200 after processing (or queuing). "
               "Return 200 for unrecognized event types too.",
    },
    {
        "id": "synchronous-processing",
        "severity": "WARNING",
        "pattern": re.compile(r"await\s+send_email|await\s+db\.|await\s+stripe\.subscriptions|sendEmail|updateDatabase"),
        "message": "Heavy processing in webhook handler — risks timeout, Stripe retries.",
        "fix": "Queue the event immediately, return 200, then process asynchronously "
               "(Celery, BullMQ, Cloud Tasks, etc.).",
    },
    {
        "id": "secret-hardcoded",
        "severity": "CRITICAL",
        "pattern": re.compile(r"whsec_[a-zA-Z0-9]{20,}|webhook_secret\s*=\s*['\"][^'\"]{10,}['\"]"),
        "message": "Webhook secret hardcoded in source — will be committed to git.",
        "fix": "Load from environment: process.env.STRIPE_WEBHOOK_SECRET or os.environ['STRIPE_WEBHOOK_SECRET']",
    },
]


def detect_lang(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext in {".ts", ".tsx", ".js", ".jsx", ".mjs"}:
        return "typescript"
    return "python"


def validate_file(path: str) -> ValidationReport:
    lang = detect_lang(path)
    report = ValidationReport(path=path, lang=lang)

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            lines = content.splitlines()
    except OSError:
        return report

    for rule in VALIDATION_RULES:
        # Signature check — language-specific absent pattern
        if rule["id"] == "missing-signature-verification":
            absent_pattern = rule["python_absent"] if lang == "python" else rule["ts_absent"]
            if not absent_pattern.search(content):
                report.issues.append(Issue(
                    severity=rule["severity"],
                    rule=rule["id"],
                    line=1,
                    message=rule["message"],
                    fix=rule["fix"],
                ))
            continue

        pattern = rule.get("pattern")
        is_absent_check = rule.get("absent", False)

        if is_absent_check:
            if pattern and not pattern.search(content):
                report.issues.append(Issue(
                    severity=rule["severity"],
                    rule=rule["id"],
                    line=1,
                    message=rule["message"],
                    fix=rule["fix"],
                ))
        elif pattern:
            for m in pattern.finditer(content):
                lineno = content[: m.start()].count("\n") + 1
                report.issues.append(Issue(
                    severity=rule["severity"],
                    rule=rule["id"],
                    line=lineno,
                    message=rule["message"],
                    fix=rule["fix"],
                ))
                break  # report once per file

    return report


# ---------------------------------------------------------------------------
# Scaffold generators
# ---------------------------------------------------------------------------

def scaffold_python(events: List[str]) -> str:
    event_handlers = []
    for ev in events:
        fn_name = ev.replace(".", "_").replace("-", "_")
        desc = STRIPE_EVENTS.get(ev, "Handle this event")
        event_handlers.append(f'''
def handle_{fn_name}(event: stripe.Event) -> None:
    """Handle {ev} — {desc}."""
    obj = event["data"]["object"]
    # TODO: implement handler
    pass
''')

    routing_cases = "\n".join(
        f'    elif event.type == "{ev}":\n        handle_{ev.replace(".", "_").replace("-", "_")}(event)'
        for ev in events
    )

    handlers_code = "\n".join(event_handlers)

    return f'''"""
Stripe webhook handler — generated by stripe_webhook_validator.py
Handles: {", ".join(events)}

Install: pip install stripe flask
Set env: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
"""

import os
import stripe
from flask import Flask, request, jsonify

app = Flask(__name__)
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
WEBHOOK_SECRET = os.environ["STRIPE_WEBHOOK_SECRET"]

# In-memory idempotency store (replace with Redis/DB in production)
_processed_event_ids: set = set()


@app.post("/webhooks/stripe")
def stripe_webhook():
    payload = request.get_data()  # raw bytes — must be before any JSON parsing
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        return jsonify({{"error": "Invalid signature"}}), 400
    except ValueError:
        return jsonify({{"error": "Invalid payload"}}), 400

    # Idempotency guard
    if event.id in _processed_event_ids:
        return jsonify({{"status": "duplicate"}}), 200
    _processed_event_ids.add(event.id)

    # Route by event type
    if False:
        pass
{routing_cases}
    else:
        # Unknown event type — return 200 to acknowledge receipt
        pass

    return jsonify({{"status": "ok"}}), 200

{handlers_code}

if __name__ == "__main__":
    app.run(port=4242, debug=False)
'''


def scaffold_typescript(events: List[str]) -> str:
    event_handlers = []
    for ev in events:
        fn_name = "handle" + "".join(w.capitalize() for w in re.split(r"[._\-]", ev))
        desc = STRIPE_EVENTS.get(ev, "Handle this event")
        event_handlers.append(f'''
async function {fn_name}(event: Stripe.Event): Promise<void> {{
  // {ev} — {desc}
  const obj = event.data.object as Stripe.Subscription; // cast to correct type
  // TODO: implement handler
}}
''')

    def ts_handler_name(ev: str) -> str:
        return "handle" + "".join(w.capitalize() for w in re.split(r"[._\-]", ev))

    routing_cases = "\n".join(
        f'    case "{ev}":\n      await {ts_handler_name(ev)}(event);\n      break;'
        for ev in events
    )

    handlers_code = "\n".join(event_handlers)

    return f'''/**
 * Stripe webhook handler — generated by stripe_webhook_validator.py
 * Handles: {", ".join(events)}
 *
 * Next.js App Router: save as app/api/webhooks/stripe/route.ts
 * Install: npm install stripe
 * Set env: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
 */

import Stripe from "stripe";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {{
  apiVersion: "2024-04-10",
}});

// In-memory idempotency store (replace with Redis/DB in production)
const processedEventIds = new Set<string>();

export async function POST(request: Request) {{
  const payload = await request.text(); // raw string — before any JSON.parse
  const sig = request.headers.get("stripe-signature") ?? "";

  let event: Stripe.Event;
  try {{
    event = stripe.webhooks.constructEvent(
      payload,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  }} catch (err) {{
    console.error("Stripe signature verification failed:", err);
    return new Response("Invalid signature", {{ status: 400 }});
  }}

  // Idempotency guard
  if (processedEventIds.has(event.id)) {{
    return new Response(JSON.stringify({{ status: "duplicate" }}), {{ status: 200 }});
  }}
  processedEventIds.add(event.id);

  // Route by event type
  switch (event.type) {{
{routing_cases}
    default:
      // Unknown event — acknowledge without processing
      break;
  }}

  return new Response(JSON.stringify({{ status: "ok" }}), {{ status: 200 }});
}}

{handlers_code}
'''


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

SEV_ICONS = {"CRITICAL": "✗✗", "WARNING": "✗ ", "NOTE": "⚠ "}


def print_validation_text(report: ValidationReport) -> int:
    criticals = report.by_severity("CRITICAL")
    warnings = report.by_severity("WARNING")
    notes = report.by_severity("NOTE")

    print(f"\nStripe Webhook Validator")
    print(f"{'=' * 55}")
    print(f"File:     {report.path}")
    print(f"Language: {report.lang}")
    print(f"Verdict:  {report.verdict}")
    print(f"Issues:   {len(criticals)} CRITICAL  {len(warnings)} WARNING  {len(notes)} NOTE\n")

    if not report.issues:
        print("No issues found.")
        return 0

    for issue in sorted(report.issues, key=lambda i: (i.severity != "CRITICAL", i.severity != "WARNING")):
        icon = SEV_ICONS.get(issue.severity, "  ")
        print(f"  {icon} [{issue.severity}] Line {issue.line}  [{issue.rule}]")
        print(f"       {issue.message}")
        print(f"       → {issue.fix}\n")

    return 1 if criticals else 0


def list_events():
    print("\nStripe event types:\n")
    for ev, desc in sorted(STRIPE_EVENTS.items()):
        critical_marker = " ⚡ (critical)" if ev in CRITICAL_EVENTS else ""
        print(f"  {ev:<45}  {desc}{critical_marker}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Stripe webhook handler validator and scaffold generator"
    )
    subparsers = parser.add_subparsers(dest="command")

    # validate
    val_parser = subparsers.add_parser("validate", help="Analyze existing webhook handler")
    val_parser.add_argument("path", help="Path to webhook handler file")
    val_parser.add_argument("--output", choices=["text", "json"], default="text")

    # scaffold
    scaf_parser = subparsers.add_parser("scaffold", help="Generate webhook handler scaffold")
    scaf_parser.add_argument(
        "--lang",
        choices=["python", "typescript"],
        default="typescript",
        help="Output language (default: typescript)",
    )
    scaf_parser.add_argument(
        "--events",
        default="checkout.session.completed,customer.subscription.updated,customer.subscription.deleted,invoice.payment_failed",
        help="Comma-separated Stripe event types",
    )
    scaf_parser.add_argument("--output", help="Write to file instead of stdout")

    # events
    subparsers.add_parser("events", help="List all supported event types")

    args = parser.parse_args()

    if args.command == "validate":
        report = validate_file(args.path)
        if args.output == "json":
            print(json.dumps({
                "path": report.path,
                "lang": report.lang,
                "verdict": report.verdict,
                "issues": [
                    {"severity": i.severity, "rule": i.rule, "line": i.line,
                     "message": i.message, "fix": i.fix}
                    for i in report.issues
                ],
            }, indent=2))
            sys.exit(1 if report.by_severity("CRITICAL") else 0)
        else:
            sys.exit(print_validation_text(report))

    elif args.command == "scaffold":
        events = [e.strip() for e in args.events.split(",") if e.strip()]
        unknown = [e for e in events if e not in STRIPE_EVENTS]
        if unknown:
            print(f"Warning: unknown event types: {', '.join(unknown)}", file=sys.stderr)

        if args.lang == "python":
            content = scaffold_python(events)
        else:
            content = scaffold_typescript(events)

        if args.output:
            with open(args.output, "w") as f:
                f.write(content)
            print(f"Written to {args.output}")
        else:
            print(content)

    elif args.command == "events":
        list_events()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
