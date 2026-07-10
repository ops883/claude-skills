---
name: case-status
description: Look up USCIS case status by receipt number — via the official USCIS Case Status API when credentials are configured, otherwise via the public egov.uscis.gov portal (Playwright). Use for "what's the status of receipt X," batch status checks across a client's cases, or monitoring a pending filing.
---

# USCIS Case Status Lookup — Law Offices of José R. Santiago

Retrieves the current USCIS status for one or more receipt numbers. Two paths: the **official API** (preferred, once onboarded) and a **public-portal fallback** (works today). Your job is to fetch and report status — the attorney interprets what it means for the case. This is not legal advice.

## When to use
Triggers: case status, receipt number, "where is my case," status check, IOE/EAC/WAC/LIN/SRC/MSC receipt, batch status, is it approved/RFE/denied.

## Receipt number format
3 service-center letters + 10 digits — e.g., `EAC9999103402`, `IOE0912345678`. Validate before querying; reject malformed numbers (they identify a client — treat as PII).

## Path A — Official USCIS Case Status API (preferred)
Use the self-contained helper shipped with this skill, `scripts/uscis_case_status.py` (stdlib only — works remotely with no install), which does the OAuth 2.0 client-credentials flow (token cached ~30 min) and `GET /case-status/{receipt}`:
```bash
export USCIS_CLIENT_ID=... USCIS_CLIENT_SECRET=...   # from the firm's Developer Team App
python3 "${CLAUDE_PLUGIN_ROOT:-.}/skills/case-status/scripts/uscis_case_status.py" EAC9999103402 [more receipts...]
```
- Defaults to **sandbox** (`api-int.uscis.gov`). For production, set `USCIS_OAUTH_URL` / `USCIS_API_BASE` to the prod URLs USCIS provides after the demo.
- If it exits with "credentials not set," the firm hasn't onboarded yet → use Path B and surface the onboarding steps below.

### Onboarding to production (gated — one-time)
1. Register a **Developer Team App** at https://developer.uscis.gov and select the **Case Status API** product (grants sandbox access immediately; issues Client ID + Secret).
2. Build/test against sandbox.
3. **Pass the USCIS demo** (demo appointments are limited, ~Wed/Thu 1–2 PM EST) to unlock production credentials and the production base URL.
4. Store the prod Client ID/Secret as env vars (never commit them); set `USCIS_OAUTH_URL` / `USCIS_API_BASE` to prod.

## Path B — Public portal fallback (works now, no onboarding)
Use the **playwright** MCP (already allow-listed for `egov.uscis.gov`) to read the public case-status page:
1. Navigate to `https://egov.uscis.gov/casestatus/landing.do`.
2. Enter the receipt number, submit, and read the status heading + paragraph.
3. Report verbatim; do not paraphrase the official status text.
- One receipt per lookup; loop for batches. This is screen-reading a public page — slower and less structured than the API, but needs no credentials.

## Output format
- **Per receipt:** `receipt | form/type (if shown) | status | status date (if shown) | source (API/portal)`.
- For batches, a table sorted by urgency (RFE/NOID/denial first).
- **Plain-language note** for any actionable status (e.g., "RFE issued → route to [rfe-response] and check the response deadline"), flagged for attorney.
- If a lookup fails, say so explicitly with the receipt and the error — never invent a status.

## Guardrails (do not skip)
- **Never fabricate or guess a status.** Report only what the API/portal returns; on failure, report the failure.
- Receipt and case details are **confidential PII** — keep output in the secure case environment; do not send to external channels.
- API credentials live in env vars only — never hard-code or commit them.
- Fetch-and-report only — the attorney interprets status and decides next action. Not legal advice.
