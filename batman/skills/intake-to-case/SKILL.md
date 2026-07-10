---
name: intake-to-case
description: Turn a raw client intake (notes, questionnaire, consultation transcript) into a structured case summary — biographic profile, immigration history timeline, eligibility flags, red flags, and a recommended next step. Use at the start of a new matter or when asked to summarize/organize an intake or open a case file.
---

# Intake → Case Summary — Law Offices of José R. Santiago

Converts unstructured client intake into a clean, structured case summary the legal team can act on. This is the front door that feeds [nta-review], [aos-audit], and [rfe-response]. Your job is to organize facts and surface flags — the attorney determines eligibility and strategy. This is not legal advice.

## When to use
A new client's intake notes, questionnaire, or consultation transcript needs to be organized into a case file. Triggers: intake, new client, consultation, "open a case," summarize this client, questionnaire, screening.

## Inputs to gather first
1. **The intake material** (notes/transcript/form). If long (>~20k tokens), don't slurp it whole — land it on disk and read selectively (Grep for the sections that matter, Read with `offset`/`limit`, summarize in passes). *(Remote profile: the desktop `headroom` proxy is not available; use this native compression instead.)*
2. **What the client wants** — the benefit/goal in their words (work permit, green card, defend deportation, citizenship, asylum, bring family).
3. Note what is **missing** — intake is rarely complete; flag gaps rather than guessing.

## What to extract
Pull these into structured fields (mark unknowns as ⬜ NEEDS-INFO; never invent):

- **Biographic:** full legal name (as on passport — note Spanish double-surnames), DOB, country of birth, nationality, A-number (if any), current address, languages, contact.
- **Immigration history timeline:** entries/exits (date, port, manner — inspected/EWI/parole), current status and expiration, prior visas, prior filings (receipt numbers), prior denials, prior removal/deportation orders, any time in detention.
- **Status of any pending action:** is there an NTA / court date / RFE / interview scheduled? → route to the matching skill ([nta-review] / [rfe-response]).
- **Family:** spouse, children, parents — status of each (USC / LPR / pending / undocumented), since qualifying relationships drive eligibility.
- **Goal & possible paths:** what the client wants; candidate benefit categories to evaluate (attorney confirms).

## Eligibility flags (surface, do not decide)
Note facts that point toward or against common relief, each tagged "attorney to verify":
- Family-based (IR/CR/F2A/F-categories) — qualifying USC/LPR relative
- Employment-based — employer/petition
- Humanitarian — asylum (1-year filing deadline flag), VAWA, U-visa, T-visa, TPS
- In removal — cancellation of removal (continuous-presence math via the deterministic `datetime` snippet below), adjustment, voluntary departure
- Naturalization — LPR duration, physical presence, good moral character window

## Red flags to surface prominently (🔴)
Criminal history, prior removal/deportation order, prior fraud/misrepresentation, unlawful presence bars (3/10-year), missed prior deadlines, prior pro-se filings, aggravated felony exposure, prior immigration-court absentia order. These change everything — flag for attorney immediately.

## Compute dates and check for a prior file
- Continuous-presence / deadline math (asylum 1-year, cancellation 10-year) — use **deterministic date arithmetic** run inline via Bash. Do not reach for the desktop `agents.analyze_request` router (not present remotely, and a router misfires on words like "removal"):
  ```python
  from datetime import date
  entry = date(2015, 1, 10)   # documented entry — verify vs I-94
  days = (date.today() - entry).days
  asylum_deadline = entry.replace(year=entry.year + 1)
  print(f"{days//365}y {(days%365)//30}m presence; meets 10-yr (3650d): {days>=3650}; asylum 1-yr deadline: {asylum_deadline}")
  ```
- Check for an existing case file before creating a new summary. *(Remote profile: firm files are not on local disk — search **Google Drive MCP** (`search_files`) for the client's existing `Client_Cases` folder; if Drive isn't connected, ask Francisco to attach the prior file rather than assuming none exists.)*

## Output format
- **Client header:** name, A#, country, DOB, languages, contact, intake date.
- **Goal (client's words) + candidate paths** (attorney to confirm).
- **Immigration history timeline** (chronological table: date · event · source/evidence · ⬜ if unverified).
- **Family table:** relation · name · status · relevance.
- **Eligibility flags:** path · supporting facts · against facts · "attorney to verify."
- **🔴 Red flags** (prominent, top if any exist).
- **Missing info checklist** — documents/answers to collect (passport, I-94, prior receipts, court docs, certificates).
- **Recommended next step** — single clearest action (e.g., "pull I-94 + run [nta-review]"; "schedule attorney consult on cancellation eligibility").

## Guardrails (do not skip)
- **Organize and flag only — the attorney decides eligibility and strategy.**
- Never state the client "qualifies" or "is eligible" — say "facts suggest X; attorney to verify."
- Mark every unknown as NEEDS-INFO; do not fill gaps with assumptions.
- Handle as confidential client PII. Internal work product, not legal advice.
