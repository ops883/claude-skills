---
name: aos-audit
description: Audit an Adjustment of Status (I-485) package form-by-form and exhibit-by-exhibit against the firm's checklist before mailing — flags missing/defective components by severity and produces a pre-mailing action list. Use when reviewing an AOS/green-card packet, a concurrent I-130/I-485/I-765 filing, or any "is this package ready to mail" request.
---

# AOS Compliance Audit — Law Offices of José R. Santiago

Codifies the firm's pre-mailing audit of an Adjustment of Status package. Goal: confirm every required component is **present, correct, and internally consistent** before the two-attorney sign-off and mailing. This is not legal advice.

## When to use
The user has an AOS/I-485 package (often concurrent I-130/I-485/I-765) and wants it audited, verified, or checked for readiness to mail. Triggers: AOS, adjustment of status, I-485, I-130, green card package, concurrent filing, F2A/IR1/CR1, "ready to mail," cover-letter sequence.

## Inputs to gather first
1. **The package** (PDF) and the **cover letter** (it defines the required sequence and contents).
2. **Category and parties** — petitioner + beneficiary names, A-numbers, DOB, country of birth, immigrant category (IR1/CR1/F2A/etc.). Identify whether LPR or USC petitioner (affects I-864 thresholds and category).
3. If the PDF is large (>~20k tokens), don't read it whole — land it on disk and read selectively (Grep for the sections that matter, Read with `offset`/`limit`, audit form-by-form in passes). *(Remote profile: the desktop `headroom` proxy is not available; use this native compression instead.)*

## Audit method
**Form by form, exhibit by exhibit, against the cover letter sequence.** Do not assume — verify each item exists in the file and is internally consistent with every other form.

### Core checklist (adapt to the cover letter; not every case has every item)
- Cover letter (attorney, dated) — present and matches enclosed sequence
- G-28 for each represented party · G-1145 e-notification
- I-130 + I-130A (spouse supplement) — reviewed page-by-page
- I-485 — reviewed page-by-page
- I-765 (EAD) and/or I-131 (AP) if filed
- **I-864 Affidavit of Support** — sponsor income clears 125% poverty threshold for household size (compute and state the multiple)
- Supporting financials — W-2s, IRS transcripts/tax returns, pay stubs, employment letters
- Civil documents — birth certificates + **certified English translations**, marriage certificate
- Identity — photo IDs, passports (current + prior), prior EAD/SSN, I-94 records
- **Bona fides** (marriage cases) — captioned relationship photos, timeline spanning the relationship, ceremony/reception/family evidence
- **Sealed I-693 medical** (+ DS-3025 vaccination record inside the sealed envelope) — confirm sealed/unopened, signature current
- **2x2 passport-style photos** per applicant per form (A-number in pencil on back)
- **Fees** — itemize each form fee, sum the total, confirm payee "U.S. Department of Homeland Security"

### Consistency checks (run across ALL forms)
- Names spelled identically across every form — **passport is controlling**
- Addresses / ZIP codes consistent everywhere
- DOB, A-numbers, country of birth consistent
- Form sequence matches the cover letter
- Dates coherent (entry, marriage, signatures)

## Apply the compliance severity matrix (remote profile — reason it directly)
The desktop RUFLO `ComplianceAuditor` (`import agents` from `/Users/tico`) is **not
available remotely** — do not attempt to import it. Instead, apply the same
form-defect severity matrix yourself using the **Severity convention** below: walk
every checklist item, classify each defect 🔴/🟡/⚪, and cross-check for internal
consistency across all forms. For any eligibility or filing question you're unsure of,
verify against the authoritative source (uscis.gov via WebFetch for form editions/fees;
CourtListener MCP for legal authority) rather than a remembered rule.

## Output format (match the firm's audit memo)
- **Header:** Petitioner (status, A#, country, DOB), Beneficiary (A#, country, DOB), filing type & category, cover-letter date, audit date, page count.
- **Executive summary table:** outstanding items that must be added before mailing, with ❌/✅ status.
- **Manual verification checklist:** every item, `Item | Manual Check | Status` (✅ present/correct · ❌ missing/defective · ⬜ needs review).
- **Action required before mailing:** numbered, specific (e.g., obtain sealed I-693, obtain 2x2 photos), ending with "final two-attorney sign-off before USPS Certified Mail / FedEx."
- **Strengths confirmed:** bona fides depth, sponsor income multiple over threshold, documentation discipline.
- **Footer:** "Prepared by Francisco Guerrero, COO. For attorney review by José R. Santiago prior to release."

## Severity convention
🔴 Blocks mailing (missing I-693, missing photos, fee wrong, name mismatch vs. passport, missing required form) · 🟡 Fix before sign-off (inconsistent address, missing translation) · ⚪ Note.

## Guardrails (do not skip)
- **Audit only — never mail.** Output requires the firm's two-attorney sign-off before release.
- Do not assume a component is present because the cover letter lists it — verify it is physically in the file.
- Internal work product, not legal advice. Attorney José R. Santiago reviews before any release.
