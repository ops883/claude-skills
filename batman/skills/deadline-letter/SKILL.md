---
name: deadline-letter
description: Draft a client-facing next-steps / deadline letter (English + Spanish) — states the upcoming deadline, what the client must bring or do, and by when, computed with deterministic date math. Use when a case has an upcoming deadline (RFE, biometrics, interview, hearing, filing window) and the client needs written notice of required action.
---

# Client Deadline / Next-Steps Letter — Law Offices of José R. Santiago

Drafts a clear, bilingual letter telling a client what is due, what to bring, and by when. Your job is to draft for attorney review — the attorney approves before anything is sent. This is not legal advice and is not sent without sign-off.

## When to use
A case has an upcoming action the client must support: RFE response, biometrics/ASC appointment, interview, master-calendar or merits hearing, a filing window opening (priority date), document collection deadline. Triggers: "letter to client," next steps, deadline notice, what to bring, recordatorio, carta al cliente.

## Inputs to gather first
1. **Client name + matter** and **language** (firm clients are largely Spanish-speaking → default to **bilingual EN/ES**; confirm).
2. **The deadline date and what it is** (RFE due, biometrics date, interview date, hearing date, filing window).
3. **What the client must do/bring** — specific documents, fees, appearance, signatures.
4. **An internal buffer** — the client-facing "please respond by" date should be **before** the true deadline so the firm has time to review and file.

## Compute dates deterministically
Do not estimate. Compute days remaining and the internal request date directly:
```python
from datetime import date, timedelta
deadline = date(2026, 8, 15)        # the true USCIS/court deadline
buffer_days = 14                    # firm review + prep time
respond_by = deadline - timedelta(days=buffer_days)
print(f"{(deadline - date.today()).days} days out; ask client to respond by {respond_by}")
```
Pick the buffer by urgency: hearings/RFEs → larger buffer; simple document drop-off → smaller.

## Letter structure (mirror in both languages)
1. **Letterhead + date** — Law Offices of José R. Santiago.
2. **Re:** client name, matter, A-number (redact in any non-secure channel), case/receipt number.
3. **What is happening** — plain language: "USCIS has requested…", "Your interview is scheduled for…".
4. **The deadline** — the date in bold, and the **firm's earlier "please respond by" date**.
5. **What you must do / bring** — numbered, concrete list.
6. **Consequence of missing it** — factual, not alarming ("If we do not receive these by X, USCIS may deny the case").
7. **How to reach us** — firm contact; instruction to call with questions.
8. **Signature block** — attorney/COO, "for attorney review."

## Output format
- Provide the letter in **two columns or two stacked sections: English, then Spanish** — same content, natural Spanish (not machine-literal).
- Use plain language at a client reading level; avoid statutory citations in the client letter.
- End with a **draft watermark line**: "DRAFT — for attorney review before sending."

## Guardrails (do not skip)
- **Draft only — never send.** The attorney approves every client communication before it goes out.
- **Do not give the client legal advice or predict outcomes** — state facts, dates, and required actions only.
- Handle the A-number and case details as confidential PII; do not transmit over insecure channels.
- Compute the deadline with the deterministic snippet above; surface days-remaining prominently. A wrong date in a client letter is a serious error.
- Internal work product until attorney sign-off.
