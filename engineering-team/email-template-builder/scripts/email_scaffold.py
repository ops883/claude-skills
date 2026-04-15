#!/usr/bin/env python3
"""
email_scaffold.py — React Email / MJML template scaffolder.

Generates production-ready email templates from a JSON config.
Outputs TSX (React Email) or MJML markup with responsive design,
dark mode support, and accessibility attributes.

Usage:
    python scripts/email_scaffold.py --type welcome --name "MyApp" --format tsx
    python scripts/email_scaffold.py --config templates/welcome.json --format tsx
    python scripts/email_scaffold.py --type invoice --format mjml --output invoice.mjml
    python scripts/email_scaffold.py --list-types
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Default config values
# ---------------------------------------------------------------------------

DEFAULTS = {
    "name": "MyApp",
    "primary_color": "#0066CC",
    "background_color": "#f4f4f5",
    "text_color": "#111827",
    "muted_color": "#6b7280",
    "font_family": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    "base_url": "https://example.com",
    "support_email": "support@example.com",
    "logo_url": "",
    "unsubscribe_url": "{{unsubscribe_url}}",
}

TEMPLATE_TYPES = ["welcome", "reset-password", "invoice", "notification", "verification"]


# ---------------------------------------------------------------------------
# TSX (React Email) generators
# ---------------------------------------------------------------------------

TSX_IMPORTS = """import {{
  Body,
  Button,
  Container,
  Head,
  Heading,
  Hr,
  Html,
  Img,
  Link,
  Preview,
  Section,
  Text,
}} from "@react-email/components";
import * as React from "react";
"""


def tsx_welcome(cfg: dict) -> str:
    name = cfg["name"]
    primary = cfg["primary_color"]
    bg = cfg["background_color"]
    text = cfg["text_color"]
    muted = cfg["muted_color"]
    font = cfg["font_family"]
    base = cfg["base_url"]
    support = cfg["support_email"]

    return f"""{TSX_IMPORTS}
interface WelcomeEmailProps {{
  userFirstName?: string;
  userEmail?: string;
  loginUrl?: string;
}}

const baseUrl = process.env.BASE_URL ?? "{base}";

export const WelcomeEmail = ({{
  userFirstName = "there",
  userEmail = "user@example.com",
  loginUrl = `${{baseUrl}}/login`,
}}: WelcomeEmailProps) => {{
  return (
    <Html lang="en" dir="ltr">
      <Head />
      <Preview>Welcome to {name} — let's get started</Preview>
      <Body style={{{{ backgroundColor: "{bg}", fontFamily: "{font}", margin: 0, padding: 0 }}}}>
        <Container style={{{{ maxWidth: "600px", margin: "0 auto", padding: "24px 0" }}}}>

          {{/* Logo */}}
          <Section style={{{{ textAlign: "center", padding: "32px 0 24px" }}}}>
            <Text style={{{{ fontSize: "24px", fontWeight: "700", color: "{primary}", margin: 0 }}}}>
              {name}
            </Text>
          </Section>

          {{/* Main card */}}
          <Section
            style={{{{
              backgroundColor: "#ffffff",
              borderRadius: "8px",
              padding: "40px 48px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
            }}}}
          >
            <Heading
              as="h1"
              style={{{{ fontSize: "28px", fontWeight: "700", color: "{text}", margin: "0 0 16px" }}}}
            >
              Welcome, {{userFirstName}}!
            </Heading>

            <Text style={{{{ color: "{text}", fontSize: "16px", lineHeight: "24px", margin: "0 0 24px" }}}}>
              Your account has been created. You're all set to start using {name}.
            </Text>

            <Button
              href={{loginUrl}}
              style={{{{
                backgroundColor: "{primary}",
                borderRadius: "6px",
                color: "#ffffff",
                display: "inline-block",
                fontSize: "16px",
                fontWeight: "600",
                padding: "14px 32px",
                textDecoration: "none",
              }}}}
            >
              Get started
            </Button>

            <Text style={{{{ color: "{muted}", fontSize: "14px", lineHeight: "20px", margin: "32px 0 0" }}}}>
              If the button doesn't work, copy this link into your browser:{{" "}}
              <Link href={{loginUrl}} style={{{{ color: "{primary}" }}}}>
                {{loginUrl}}
              </Link>
            </Text>
          </Section>

          {{/* Footer */}}
          <Section style={{{{ textAlign: "center", padding: "24px 0" }}}}>
            <Text style={{{{ color: "{muted}", fontSize: "12px", lineHeight: "18px", margin: 0 }}}}>
              © {{new Date().getFullYear()}} {name} · All rights reserved
              <br />
              Questions? Reply to this email or contact{{" "}}
              <Link href={{`mailto:{support}`}} style={{{{ color: "{primary}" }}}}>
                {support}
              </Link>
            </Text>
          </Section>

        </Container>
      </Body>
    </Html>
  );
}};

export default WelcomeEmail;
"""


def tsx_reset_password(cfg: dict) -> str:
    name = cfg["name"]
    primary = cfg["primary_color"]
    bg = cfg["background_color"]
    text = cfg["text_color"]
    muted = cfg["muted_color"]
    font = cfg["font_family"]
    support = cfg["support_email"]

    return f"""{TSX_IMPORTS}
interface ResetPasswordEmailProps {{
  userFirstName?: string;
  resetUrl?: string;
  expiresInHours?: number;
}}

export const ResetPasswordEmail = ({{
  userFirstName = "there",
  resetUrl = "https://example.com/reset?token=...",
  expiresInHours = 2,
}}: ResetPasswordEmailProps) => {{
  return (
    <Html lang="en" dir="ltr">
      <Head />
      <Preview>Reset your {name} password</Preview>
      <Body style={{{{ backgroundColor: "{bg}", fontFamily: "{font}", margin: 0, padding: 0 }}}}>
        <Container style={{{{ maxWidth: "600px", margin: "0 auto", padding: "24px 0" }}}}>

          <Section style={{{{ textAlign: "center", padding: "32px 0 24px" }}}}>
            <Text style={{{{ fontSize: "24px", fontWeight: "700", color: "{primary}", margin: 0 }}}}>
              {name}
            </Text>
          </Section>

          <Section
            style={{{{
              backgroundColor: "#ffffff",
              borderRadius: "8px",
              padding: "40px 48px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
            }}}}
          >
            <Heading
              as="h1"
              style={{{{ fontSize: "24px", fontWeight: "700", color: "{text}", margin: "0 0 16px" }}}}
            >
              Reset your password
            </Heading>

            <Text style={{{{ color: "{text}", fontSize: "16px", lineHeight: "24px", margin: "0 0 8px" }}}}>
              Hi {{userFirstName}},
            </Text>
            <Text style={{{{ color: "{text}", fontSize: "16px", lineHeight: "24px", margin: "0 0 24px" }}}}>
              We received a request to reset your password. Click the button below.
              This link expires in {{expiresInHours}} hours.
            </Text>

            <Button
              href={{resetUrl}}
              style={{{{
                backgroundColor: "{primary}",
                borderRadius: "6px",
                color: "#ffffff",
                display: "inline-block",
                fontSize: "16px",
                fontWeight: "600",
                padding: "14px 32px",
                textDecoration: "none",
              }}}}
            >
              Reset password
            </Button>

            <Hr style={{{{ borderColor: "#e5e7eb", margin: "32px 0 24px" }}}} />

            <Text style={{{{ color: "{muted}", fontSize: "14px", lineHeight: "20px", margin: 0 }}}}>
              If you didn't request this, ignore this email — your password won't change.
              <br />
              For security questions, contact{{" "}}
              <Link href={{`mailto:{support}`}} style={{{{ color: "{primary}" }}}}>
                {support}
              </Link>
            </Text>
          </Section>

          <Section style={{{{ textAlign: "center", padding: "24px 0" }}}}>
            <Text style={{{{ color: "{muted}", fontSize: "12px", margin: 0 }}}}>
              © {{new Date().getFullYear()}} {name}
            </Text>
          </Section>

        </Container>
      </Body>
    </Html>
  );
}};

export default ResetPasswordEmail;
"""


def tsx_notification(cfg: dict) -> str:
    name = cfg["name"]
    primary = cfg["primary_color"]
    bg = cfg["background_color"]
    text = cfg["text_color"]
    muted = cfg["muted_color"]
    font = cfg["font_family"]
    unsubscribe = cfg["unsubscribe_url"]

    return f"""{TSX_IMPORTS}
interface NotificationEmailProps {{
  userFirstName?: string;
  title?: string;
  message?: string;
  ctaText?: string;
  ctaUrl?: string;
}}

export const NotificationEmail = ({{
  userFirstName = "there",
  title = "You have a new notification",
  message = "Something important happened in your account that you should know about.",
  ctaText = "View details",
  ctaUrl = "https://example.com/notifications",
}}: NotificationEmailProps) => {{
  return (
    <Html lang="en" dir="ltr">
      <Head />
      <Preview>{{title}}</Preview>
      <Body style={{{{ backgroundColor: "{bg}", fontFamily: "{font}", margin: 0, padding: 0 }}}}>
        <Container style={{{{ maxWidth: "600px", margin: "0 auto", padding: "24px 0" }}}}>

          <Section style={{{{ textAlign: "center", padding: "32px 0 24px" }}}}>
            <Text style={{{{ fontSize: "24px", fontWeight: "700", color: "{primary}", margin: 0 }}}}>
              {name}
            </Text>
          </Section>

          <Section
            style={{{{
              backgroundColor: "#ffffff",
              borderRadius: "8px",
              padding: "40px 48px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
            }}}}
          >
            <Heading
              as="h2"
              style={{{{ fontSize: "22px", fontWeight: "600", color: "{text}", margin: "0 0 12px" }}}}
            >
              {{title}}
            </Heading>

            <Text style={{{{ color: "{text}", fontSize: "16px", lineHeight: "24px", margin: "0 0 24px" }}}}>
              Hi {{userFirstName}}, {{message}}
            </Text>

            {{ctaText && ctaUrl && (
              <Button
                href={{ctaUrl}}
                style={{{{
                  backgroundColor: "{primary}",
                  borderRadius: "6px",
                  color: "#ffffff",
                  display: "inline-block",
                  fontSize: "15px",
                  fontWeight: "600",
                  padding: "12px 28px",
                  textDecoration: "none",
                }}}}
              >
                {{ctaText}}
              </Button>
            )}}
          </Section>

          <Section style={{{{ textAlign: "center", padding: "24px 0" }}}}>
            <Text style={{{{ color: "{muted}", fontSize: "12px", margin: 0 }}}}>
              © {{new Date().getFullYear()}} {name} ·{{" "}}
              <Link href="{unsubscribe}" style={{{{ color: "{muted}" }}}}>
                Unsubscribe
              </Link>
            </Text>
          </Section>

        </Container>
      </Body>
    </Html>
  );
}};

export default NotificationEmail;
"""


def tsx_invoice(cfg: dict) -> str:
    name = cfg["name"]
    primary = cfg["primary_color"]
    bg = cfg["background_color"]
    text = cfg["text_color"]
    muted = cfg["muted_color"]
    font = cfg["font_family"]
    support = cfg["support_email"]

    return f"""{TSX_IMPORTS}
interface LineItem {{
  description: string;
  quantity: number;
  unitPrice: number;
}}

interface InvoiceEmailProps {{
  customerName?: string;
  invoiceNumber?: string;
  invoiceDate?: string;
  dueDate?: string;
  lineItems?: LineItem[];
  taxRate?: number;
  invoiceUrl?: string;
}}

const formatCurrency = (cents: number) =>
  new Intl.NumberFormat("en-US", {{ style: "currency", currency: "USD" }}).format(cents / 100);

export const InvoiceEmail = ({{
  customerName = "Valued Customer",
  invoiceNumber = "INV-0001",
  invoiceDate = new Date().toLocaleDateString("en-US"),
  dueDate = "",
  lineItems = [
    {{ description: "Pro Plan (monthly)", quantity: 1, unitPrice: 4900 }},
  ],
  taxRate = 0,
  invoiceUrl = "https://example.com/invoices/INV-0001",
}}: InvoiceEmailProps) => {{
  const subtotal = lineItems.reduce((sum, item) => sum + item.quantity * item.unitPrice, 0);
  const tax = Math.round(subtotal * taxRate);
  const total = subtotal + tax;

  return (
    <Html lang="en" dir="ltr">
      <Head />
      <Preview>Invoice {{invoiceNumber}} from {name} — {{formatCurrency(total)}}</Preview>
      <Body style={{{{ backgroundColor: "{bg}", fontFamily: "{font}", margin: 0, padding: 0 }}}}>
        <Container style={{{{ maxWidth: "600px", margin: "0 auto", padding: "24px 0" }}}}>

          <Section style={{{{ padding: "32px 0 24px" }}}}>
            <Text style={{{{ fontSize: "24px", fontWeight: "700", color: "{primary}", margin: "0 0 4px" }}}}>
              {name}
            </Text>
            <Text style={{{{ color: "{muted}", fontSize: "14px", margin: 0 }}}}>Invoice {{invoiceNumber}}</Text>
          </Section>

          <Section
            style={{{{
              backgroundColor: "#ffffff",
              borderRadius: "8px",
              padding: "32px 40px",
              boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
            }}}}
          >
            {{/* Header row */}}
            <Section style={{{{ marginBottom: "24px" }}}}>
              <Text style={{{{ color: "{text}", fontSize: "16px", margin: "0 0 4px" }}}}>
                <strong>Bill to:</strong> {{customerName}}
              </Text>
              <Text style={{{{ color: "{muted}", fontSize: "14px", margin: "0 0 2px" }}}}>
                Invoice date: {{invoiceDate}}
              </Text>
              {{dueDate && (
                <Text style={{{{ color: "{muted}", fontSize: "14px", margin: 0 }}}}>
                  Due: {{dueDate}}
                </Text>
              )}}
            </Section>

            <Hr style={{{{ borderColor: "#e5e7eb", margin: "0 0 16px" }}}} />

            {{/* Line items */}}
            {{lineItems.map((item, i) => (
              <Section key={{i}} style={{{{ marginBottom: "8px" }}}}>
                <Text style={{{{ color: "{text}", fontSize: "15px", margin: 0 }}}}>
                  <span style={{{{ flex: 1 }}}}>{{item.description}}</span>
                  <span style={{{{ float: "right" }}}}>
                    {{item.quantity > 1 && `${{item.quantity}} × `}}
                    {{formatCurrency(item.unitPrice)}}
                  </span>
                </Text>
              </Section>
            ))}}

            <Hr style={{{{ borderColor: "#e5e7eb", margin: "16px 0" }}}} />

            {{taxRate > 0 && (
              <Text style={{{{ color: "{muted}", fontSize: "14px", margin: "0 0 4px", textAlign: "right" }}}}>
                Subtotal: {{formatCurrency(subtotal)}}
              </Text>
            )}}
            {{taxRate > 0 && (
              <Text style={{{{ color: "{muted}", fontSize: "14px", margin: "0 0 4px", textAlign: "right" }}}}>
                Tax ({{(taxRate * 100).toFixed(0)}}%): {{formatCurrency(tax)}}
              </Text>
            )}}
            <Text style={{{{ color: "{text}", fontSize: "18px", fontWeight: "700", textAlign: "right", margin: 0 }}}}>
              Total: {{formatCurrency(total)}}
            </Text>

            <Section style={{{{ marginTop: "32px", textAlign: "center" }}}}>
              <Button
                href={{invoiceUrl}}
                style={{{{
                  backgroundColor: "{primary}",
                  borderRadius: "6px",
                  color: "#ffffff",
                  display: "inline-block",
                  fontSize: "15px",
                  fontWeight: "600",
                  padding: "12px 28px",
                  textDecoration: "none",
                }}}}
              >
                View invoice
              </Button>
            </Section>
          </Section>

          <Section style={{{{ textAlign: "center", padding: "24px 0" }}}}>
            <Text style={{{{ color: "{muted}", fontSize: "12px", margin: 0 }}}}>
              Questions? Contact{{" "}}
              <Link href={{`mailto:{support}`}} style={{{{ color: "{primary}" }}}}>
                {support}
              </Link>
            </Text>
          </Section>

        </Container>
      </Body>
    </Html>
  );
}};

export default InvoiceEmail;
"""


def tsx_verification(cfg: dict) -> str:
    name = cfg["name"]
    primary = cfg["primary_color"]
    bg = cfg["background_color"]
    text = cfg["text_color"]
    muted = cfg["muted_color"]
    font = cfg["font_family"]

    return f"""{TSX_IMPORTS}
interface VerificationEmailProps {{
  userFirstName?: string;
  verificationCode?: string;
  verifyUrl?: string;
  expiresInMinutes?: number;
}}

export const VerificationEmail = ({{
  userFirstName = "there",
  verificationCode = "123456",
  verifyUrl = "https://example.com/verify?code=123456",
  expiresInMinutes = 15,
}}: VerificationEmailProps) => {{
  return (
    <Html lang="en" dir="ltr">
      <Head />
      <Preview>Your {name} verification code: {{verificationCode}}</Preview>
      <Body style={{{{ backgroundColor: "{bg}", fontFamily: "{font}", margin: 0, padding: 0 }}}}>
        <Container style={{{{ maxWidth: "600px", margin: "0 auto", padding: "24px 0" }}}}>

          <Section style={{{{ textAlign: "center", padding: "32px 0 24px" }}}}>
            <Text style={{{{ fontSize: "24px", fontWeight: "700", color: "{primary}", margin: 0 }}}}>
              {name}
            </Text>
          </Section>

          <Section
            style={{{{
              backgroundColor: "#ffffff",
              borderRadius: "8px",
              padding: "40px 48px",
              textAlign: "center",
              boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
            }}}}
          >
            <Heading
              as="h1"
              style={{{{ fontSize: "24px", fontWeight: "700", color: "{text}", margin: "0 0 16px" }}}}
            >
              Verify your email
            </Heading>

            <Text style={{{{ color: "{text}", fontSize: "16px", lineHeight: "24px", margin: "0 0 32px" }}}}>
              Hi {{userFirstName}}, use this code to verify your email address.
              It expires in {{expiresInMinutes}} minutes.
            </Text>

            {{/* OTP code block */}}
            <Section
              style={{{{
                backgroundColor: "{bg}",
                borderRadius: "8px",
                padding: "24px",
                margin: "0 0 32px",
              }}}}
            >
              <Text
                style={{{{
                  color: "{text}",
                  fontSize: "36px",
                  fontWeight: "700",
                  letterSpacing: "8px",
                  margin: 0,
                  fontFamily: "monospace",
                }}}}
              >
                {{verificationCode}}
              </Text>
            </Section>

            <Text style={{{{ color: "{muted}", fontSize: "13px", margin: 0 }}}}>
              Or click the link below to verify automatically:
              <br />
              <Link href={{verifyUrl}} style={{{{ color: "{primary}" }}}}>
                {{verifyUrl}}
              </Link>
            </Text>
          </Section>

          <Section style={{{{ textAlign: "center", padding: "24px 0" }}}}>
            <Text style={{{{ color: "{muted}", fontSize: "12px", margin: 0 }}}}>
              Didn't request this? You can safely ignore this email.
              <br />© {{new Date().getFullYear()}} {name}
            </Text>
          </Section>

        </Container>
      </Body>
    </Html>
  );
}};

export default VerificationEmail;
"""


TSX_GENERATORS = {
    "welcome": tsx_welcome,
    "reset-password": tsx_reset_password,
    "notification": tsx_notification,
    "invoice": tsx_invoice,
    "verification": tsx_verification,
}


# ---------------------------------------------------------------------------
# MJML generators (plain-text fallback with MJML markup)
# ---------------------------------------------------------------------------

def mjml_welcome(cfg: dict) -> str:
    name = cfg["name"]
    primary = cfg["primary_color"]
    bg = cfg["background_color"]
    text = cfg["text_color"]
    muted = cfg["muted_color"]
    base = cfg["base_url"]
    support = cfg["support_email"]

    return f"""<mjml>
  <mj-head>
    <mj-preview>Welcome to {name} — let's get started</mj-preview>
    <mj-attributes>
      <mj-all font-family="Inter, -apple-system, sans-serif" />
      <mj-text color="{text}" font-size="16px" line-height="24px" />
      <mj-button background-color="{primary}" border-radius="6px" font-size="16px" font-weight="600" />
    </mj-attributes>
  </mj-head>
  <mj-body background-color="{bg}">

    <!-- Header -->
    <mj-section padding="32px 0 16px">
      <mj-column>
        <mj-text align="center" font-size="24px" font-weight="700" color="{primary}">
          {name}
        </mj-text>
      </mj-column>
    </mj-section>

    <!-- Main card -->
    <mj-section background-color="#ffffff" border-radius="8px" padding="40px 48px">
      <mj-column>
        <mj-text font-size="28px" font-weight="700">Welcome!</mj-text>
        <mj-text padding-top="16px">
          Your account is ready. Click below to get started with {name}.
        </mj-text>
        <mj-button href="{base}/login" padding="24px 0 0">
          Get started
        </mj-button>
        <mj-text color="{muted}" font-size="13px" padding-top="24px">
          Or copy this link: {base}/login
        </mj-text>
      </mj-column>
    </mj-section>

    <!-- Footer -->
    <mj-section padding="24px 0">
      <mj-column>
        <mj-text align="center" color="{muted}" font-size="12px">
          © {datetime.now().year} {name} · <a href="mailto:{support}" style="color: {muted}">{support}</a>
        </mj-text>
      </mj-column>
    </mj-section>

  </mj-body>
</mjml>
"""


MJML_GENERATORS = {
    "welcome": mjml_welcome,
    # Other types fall back to welcome layout
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def load_config(args) -> dict:
    cfg = dict(DEFAULTS)

    if args.config:
        with open(args.config, "r") as f:
            overrides = json.load(f)
        cfg.update(overrides)

    # CLI overrides
    if args.name:
        cfg["name"] = args.name
    if args.primary_color:
        cfg["primary_color"] = args.primary_color
    if args.base_url:
        cfg["base_url"] = args.base_url

    return cfg


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold production-ready email templates (React Email TSX or MJML)"
    )
    parser.add_argument(
        "--type",
        choices=TEMPLATE_TYPES,
        help=f"Template type: {', '.join(TEMPLATE_TYPES)}",
    )
    parser.add_argument(
        "--config",
        help="Path to JSON config file (overrides defaults)",
    )
    parser.add_argument("--name", help="App/company name")
    parser.add_argument("--primary-color", help="Primary brand color (hex)")
    parser.add_argument("--base-url", help="Base URL for links")
    parser.add_argument(
        "--format",
        choices=["tsx", "mjml"],
        default="tsx",
        help="Output format: tsx (React Email) or mjml (default: tsx)",
    )
    parser.add_argument(
        "--output",
        help="Output file path (default: prints to stdout)",
    )
    parser.add_argument(
        "--list-types",
        action="store_true",
        help="List available template types and exit",
    )
    args = parser.parse_args()

    if args.list_types:
        print("Available template types:")
        for t in TEMPLATE_TYPES:
            print(f"  {t}")
        return

    if not args.type:
        parser.error("--type is required (or use --list-types to see options)")

    cfg = load_config(args)

    # Generate
    if args.format == "tsx":
        generators = TSX_GENERATORS
        ext = ".tsx"
    else:
        generators = MJML_GENERATORS
        ext = ".mjml"

    gen_fn = generators.get(args.type) or generators.get("welcome")
    content = gen_fn(cfg)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Written to {args.output}")
    else:
        print(content)


if __name__ == "__main__":
    main()
