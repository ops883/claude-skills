---
name: form-checklist
description: Generate a filing checklist for a USCIS form or package — required form editions, supporting documents, photos, fees, and the cover-letter assembly sequence — tailored to the case category. Use when assembling a filing, asking "what do I need to file I-130/I-485/I-765/I-131/N-400," or prepping a package before the aos-audit.
---

# Filing Checklist Generator — Law Offices of José R. Santiago

Produces a build checklist for a USCIS filing so the package is assembled correctly the first time. This is the **pre-assembly** companion to [aos-audit] (which audits a finished package). Your job is to list what the filing requires — the attorney confirms eligibility and category. This is not legal advice.

## When to use
The team is about to assemble a filing and needs the component list. Triggers: "what do I need to file," checklist for I-130/I-485/I-765/I-131/I-130A/I-864/N-400/I-589/I-90/I-751, package assembly, cover letter sequence, filing fees, what supporting documents.

## Inputs to gather first
1. **Which form(s)** and whether filed standalone or **concurrent** (e.g., I-130 + I-485 + I-765 + I-131).
2. **Category / basis** — IR/CR (spouse of USC), F2A (spouse/child of LPR), employment, VAWA, asylum-based, etc. Category drives which supporting evidence is required.
3. **Petitioner/beneficiary status** — USC vs. LPR petitioner (affects I-864 thresholds and concurrent eligibility), beneficiary inside vs. outside US.
4. **⚠️ Verify the current form edition and fee** — USCIS form editions and fees change. Confirm against uscis.gov (via Playwright/WebFetch) before finalizing; do not rely on remembered fee amounts.

## What to produce
A checklist organized in **cover-letter assembly order**, with for each item: required? (✅ required / ◻️ if-applicable), what it is, and the evidence/edition note.

### Typical components (adapt to the actual case — not every filing needs every item)
- **Cover letter** (attorney, dated) listing enclosures in order
- **G-28** for each represented party · **G-1145** e-notification
- **The petition/application form(s)** — confirm current edition; signed in ink/e-sig where required
- **Supplements** — I-130A (spouse), I-864 + I-864 supporting financials (W-2s, tax transcripts, pay stubs, employment letter) for family AOS
- **Civil documents** — birth certificates, marriage certificate, divorce decrees (terminating prior marriages) — **+ certified English translations**
- **Identity** — passport bio pages, prior visas/I-94, prior EAD/SSN, photo IDs
- **Bona fides** (marriage cases) — captioned photos, joint accounts/lease/insurance, affidavits
- **Sealed I-693 medical** (+ DS-3025) for I-485 — note it can be filed concurrently or later
- **Passport-style 2x2 photos** — count per form per applicant
- **Fees** — itemize per form, sum the total, payee "U.S. Department of Homeland Security"; note fee-waiver (I-912) if applicable

### Fees & editions
Always present fees as a table the team must **verify against uscis.gov today**, with a visible "confirm current edition/fee" flag — never present a remembered number as authoritative.

## Output format
- **Header:** form(s), category/basis, standalone vs. concurrent, filing location (lockbox/service center — verify on uscis.gov).
- **Assembly checklist** in cover-letter order: `Order | Component | Required? | Edition/evidence note`.
- **Fee table:** `Form | Fee (VERIFY) | Notes` + total, with the confirm-on-uscis.gov flag.
- **Translations needed:** list every non-English civil document requiring a certified translation.
- **Hand-off:** "When assembled, run [aos-audit] before two-attorney sign-off and mailing."

## Guardrails (do not skip)
- **Verify current form edition, fee, and filing address on uscis.gov before filing** — these change and a wrong edition/fee causes rejection. Flag every fee as "verify."
- **List requirements only — the attorney confirms category and eligibility.** Do not assert the client qualifies for the benefit.
- Internal work product, not legal advice. Two-attorney sign-off before mailing.
