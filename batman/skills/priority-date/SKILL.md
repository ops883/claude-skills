---
name: priority-date
description: Check whether a client's priority date is current against the State Department Visa Bulletin — fetches the LIVE bulletin (it changes monthly), reads the correct chart (Final Action vs. Dates for Filing) for the right category and country of chargeability, and explains retrogression/movement. Use for any "is my priority date current," visa availability, or Visa Bulletin question.
---

# Priority Date / Visa Bulletin Check — Law Offices of José R. Santiago

Determines visa availability for a client by comparing their **priority date** against the current Visa Bulletin. Your job is to read the right chart correctly and explain it — the attorney advises the client. This is not legal advice.

## ⚠️ Critical: never answer from memory
The Visa Bulletin **changes every month** and categories retrogress without warning. You MUST fetch the **current** bulletin before answering. Hardcoded or remembered dates will be wrong and can cause a missed filing window or a premature filing.

## When to use
Triggers: priority date, visa bulletin, "is my date current," visa availability, retrogression, Dates for Filing, Final Action Dates, F2A/F1/F3/F4, EB-1/EB-2/EB-3, priority date current, "can I file my I-485 yet."

## Inputs to gather first
1. **Priority date** — the date the underlying petition (I-130 / I-140) was properly filed (the receipt establishes it).
2. **Category** — family (F1, F2A, F2B, F3, F4) or employment (EB-1 … EB-5), and whether immediate-relative (IR — always current, no wait).
3. **Country of chargeability** — usually country of birth, NOT nationality. Note cross-chargeability options (e.g., via spouse) if relevant.
4. **Which chart applies** — see below.

## Procedure
1. **Fetch the current bulletin.** Use WebFetch/WebSearch on `travel.state.gov` Visa Bulletin for the current month (and confirm the month/fiscal year on the page). If unreachable, say so and do not guess.
2. **Pick the correct chart:**
   - **Final Action Dates** — when a visa can actually be issued / green card approved.
   - **Dates for Filing** — when USCIS lets the applicant *submit* the AOS package. For adjustment cases, **check whether USCIS has said to use "Dates for Filing" for the current month** (USCIS announces this monthly on uscis.gov); only then is the Dates-for-Filing chart usable for I-485 filing.
3. **Find the cell** for the client's category × country of chargeability.
4. **Compare:** priority date **before** the listed cutoff date → **current** (visa available / may file, per chart). A "C" means current. A "U" means unavailable. Date listed = wait until your PD is earlier than it.
5. **Note movement/retrogression** — compare to last month if relevant; flag if the category recently retrogressed or is close.

## Output format
- **Bulletin reference:** month/year of the bulletin fetched + source URL (so the answer is auditable).
- **Client inputs:** priority date, category, country of chargeability.
- **Result table:** Chart used · category · country · cutoff date in bulletin · **Current? (Yes/No)** · how many days/months ahead or behind.
- **Plain-language answer:** e.g., "Final Action Date for F2A Mexico is 15-SEP-2021; client's PD is 03-MAR-2020 → current, visa available." or "Not current; PD must reach <date>; check again next month."
- **Filing note:** whether the client may *file* AOS now (Dates for Filing, if USCIS authorized it this month) vs. whether the case can be *approved* (Final Action).
- **Caveats:** retrogression risk; chargeability assumptions; that the bulletin updates monthly so re-check before action.

## Guardrails (do not skip)
- **Always fetch the live bulletin; cite the month and URL.** If you could not fetch it, state that and stop — do not estimate.
- Distinguish **Dates for Filing vs. Final Action** explicitly; never conflate "can file" with "can be approved."
- Country of chargeability is normally **country of birth**, not nationality — confirm.
- Read-and-explain only — the attorney advises the client and decides timing. Not legal advice.
