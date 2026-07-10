---
name: nta-review
description: Review a Notice to Appear (NTA) for factual and legal defects using the firm's checklist — flags Pereira defects, wrong 212/237 charges, entry-manner errors, and identity discrepancies. Use when an NTA enters the office, when asked to review/audit an NTA, or for removal-defense intake.
---

# NTA Review — Law Offices of José R. Santiago

Codifies the firm's internal NTA review process. Your job is to **detect and document defects** — the attorney decides strategy. This is not legal advice.

**Firm rule:** Every NTA that enters the office is reviewed with the full checklist before any other step.

## When to use
The user gives you an NTA (PDF, image, or text) — or facts about one — and wants it reviewed, or mentions: NTA, Notice to Appear, removal, deportation, master calendar, Pereira, charges, EWI, overstay, A-number defect.

## Inputs to gather first
1. **The NTA itself** — text/PDF/image. If a long PDF (>~20k tokens), don't read it whole — land it on disk and read selectively (Grep for the sections that matter, Read with `offset`/`limit`). *(Remote profile: the desktop `headroom` proxy is not available; use this native compression instead.)*
2. **The client's ground-truth facts** — name as in passport, true DOB, country of birth vs. nationality, real entry date/port/manner, A-number, I-94 status. Ask for these if not provided; the review is only as good as the comparison against truth.
3. **I-94 / passport** if available — required to verify manner and date of entry.

If client facts are missing, still review the NTA for internal/legal defects (Pereira, internal contradictions, missing sections) and flag which checks need client data to complete.

## Review procedure

Walk all 8 sections and produce findings. For each section, compare NTA text against client ground truth.

1. **Court info** — correct court for client's residence; complete address.
2. **Respondent info** — name exactly as passport (watch Spanish double-surnames and order), DOB, country of birth vs. nationality (can differ), A-number.
3. **Factual allegations** — entry date, port, **manner of entry** (the critical one: NTA says "without admission/parole" or "unknown" but client entered on B1/B2, F1, etc.), current status, family data.
4. **Charges** — is it INA 212 (inadmissibility / EWI) or INA 237 (deportability / admitted-then-violated)? Verify the charge matches documented manner of entry. **Entered on a visa → charge must be 237 (e.g., 237(a)(1)(B) overstay), not 212(a)(6)(A)(i).**
5. **Hearing date/time/place (Pereira)** — if any of date, time, or location says "To Be Determined," flag as **Pereira defect**: the stop-time clock did not stop; compute continuous-presence years from entry to today.
6. **Rights of respondent** — present and in a language the client understands.
7. **Officer signature & date** — present; issuing agency (ICE/CBP).
8. **Certificate of service** — date and method (personal vs. mail) consistent with client recollection; affects stop-time and deadline calc.

## The 8 common defects to hunt actively
1. Name misspelled/incomplete · 2. Wrong manner of entry (EWI vs. visa) · 3. Wrong entry date · 4. Wrong port of entry · 5. **Wrong charge (212 vs. 237)** · 6. **No hearing date/time (Pereira)** · 7. Wrong country of birth/nationality · 8. Internal contradictions.

## Computing continuous presence (Pereira)
Use **deterministic date arithmetic** — do NOT route through `agents.analyze_request` (a request router, not a calculator: it misfires on the word "removal" and returns low-confidence noise). Compute directly:
```python
from datetime import date
entry = date(2015, 1, 10)   # client's DOCUMENTED entry date — verify against I-94 first
today = date.today()
days = (today - entry).days
years, months = days // 365, (days % 365) // 30
print(f"Continuous presence: {years}y {months}m ({days} days); meets 10-yr (3650d) rule: {days >= 3650}")
```
For statutory **deadline windows** (asylum 1-year, I-290B 30-day appeal), compute them the same deterministic way — parse the anchor date, add the window with `datetime`, and state days remaining. The desktop RUFLO `DeadlineCalculator` is a Claude-API-backed router that is **not available remotely**; you don't need it — inline `datetime` math is authoritative and needs no key or backend.

## Output format
Produce a memo with:

- **Header:** Respondent name, A-number, country, alleged entry, charge cited.
- **Defects table:** `# | Defect | What the NTA says | What it should say | Evidence to obtain | Severity`
  - Severity: 🔴 Critical (changes charges/eligibility — manner of entry, wrong charge, Pereira) · 🟡 Material (dates, identity) · ⚪ Note (rights section, formatting).
- **Pereira analysis** (if applicable): entry date → today, total continuous presence, eligibility-timing note (attorney verifies other requirements).
- **Checklist** (full firm checklist, each item ✅/❌/⬜-needs-data).
- **Action items:** documents to pull (I-94 from cbp.gov/i94, passport, birth certificate), and "Report to attorney / Julian same day."

## Guardrails (do not skip)
- **Detect and document only — the attorney decides legal strategy.**
- **Do not advise contacting the client about an error** without attorney instruction.
- Flag every 🔴 finding explicitly as "report to attorney immediately."
- This output is internal work product, not legal advice, and requires attorney review before any action.
