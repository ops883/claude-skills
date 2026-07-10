---
name: rfe-response
description: Build the skeleton of a response to a USCIS Request for Evidence (RFE) or Notice of Intent to Deny (NOID) — parses what USCIS is asking, maps each request to an evidence checklist, computes the response deadline, and drafts a cover letter. Use when an RFE/NOID arrives or when asked to prepare/organize an RFE response.
---

# RFE / NOID Response — Law Offices of José R. Santiago

Turns a USCIS Request for Evidence or Notice of Intent to Deny into an organized, deadline-aware response plan and cover-letter draft. Your job is to structure the response and identify required evidence — the attorney approves substance and strategy. This is not legal advice.

## When to use
The user has an RFE or NOID and wants it analyzed, organized, or responded to. Triggers: RFE, Request for Evidence, NOID, Notice of Intent to Deny, "USCIS is asking for," response deadline, evidence list, I-797E.

## Inputs to gather first
1. **The RFE/NOID notice** (PDF/text) — contains the issued date, **response deadline**, receipt number, form/benefit at issue, and the itemized requests.
2. **The underlying case** — which form/benefit (I-130, I-485, I-765, I-140, I-129, N-400, asylum, etc.), category, and what was originally filed.
3. If the notice is long (>~20k tokens), don't read it whole — land it on disk and read selectively (Grep for the sections that matter, Read with `offset`/`limit`). *(Remote profile: the desktop `headroom` proxy is not available; use this native compression instead.)*

## Procedure
1. **Extract the metadata** — receipt number, benefit/form, date issued, **deadline date** (RFEs are typically up to 87 days; NOIDs commonly ~30 days — use the date printed on the notice, do not assume).
2. **Decompose the asks** — list each distinct item USCIS requests as a separate line. RFEs bundle multiple requests; treat each independently.
3. **Map each ask to evidence** — for each request, identify the specific documents/affidavits/translations that satisfy it, and whether the firm already has them on file (remote profile: search **Google Drive MCP** for the client's `Client_Cases` folder when connected) or must obtain them.
4. **Identify the legal standard** when the RFE challenges eligibility (e.g., bona fide marriage, ability to pay, qualifying relationship, maintenance of status) — note what the controlling standard requires so evidence is targeted, not generic.
5. **Compute the deadline** with **deterministic date arithmetic** (not `agents.analyze_request` — a router, not a calculator) and set an internal deadline **before** the USCIS date. The due date is printed on the notice; trust it over any computed estimate:
   ```python
   from datetime import date, timedelta
   due = date(2026, 8, 15)   # the response-due date printed on the RFE/NOID
   days_left = (due - date.today()).days
   internal = due - timedelta(days=7)   # buffer for two-attorney review + mailing
   print(f"{days_left} days to USCIS deadline; internal target {internal}")
   ```
6. **Draft the cover letter** — addressed to the USCIS office/lockbox on the notice, referencing the receipt number, listing enclosures in the order USCIS asked, and stating that the response is timely.

## Output format
- **RFE summary header:** receipt number, benefit/form, date issued, **response deadline (with days remaining and a recommended internal deadline)**, urgency flag.
- **Request → evidence matrix:**
  `# | What USCIS asks | Legal standard / why | Evidence to satisfy it | On file? | To obtain | Owner`
- **Gap list:** items not yet in hand, who obtains them, by when.
- **Cover-letter draft:** ready for attorney edit — caption, receipt number, itemized enclosures matching USCIS's order, timeliness statement, attorney signature block.
- **Risk notes:** anything that reads like a NOID-level challenge to eligibility (flag for attorney; these are not routine document requests).

## Urgency convention
🔴 <14 days to deadline · 🟡 14–30 days · 🟢 >30 days. Always recommend an internal deadline with buffer for two-attorney review and mailing time.

## Guardrails (do not skip)
- **Deadlines are absolute.** Always surface the response deadline first and flag if it is near or ambiguous. A missed RFE deadline can deny the case.
- **Structure and evidence-mapping only — the attorney approves substance, legal arguments, and final submission.**
- Do not fabricate or assume evidence exists; mark "on file?" honestly and verify against the case folder.
- Internal work product, not legal advice. Two-attorney sign-off before mailing.
