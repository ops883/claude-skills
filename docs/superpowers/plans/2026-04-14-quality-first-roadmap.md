# Quality-First Roadmap — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consolidate conflicting standards docs, tighten CI linting, fix count inconsistencies, and establish a repeatable per-domain quality audit process.

**Architecture:** Two phases. Phase 1 is pure file edits (docs + one test file) with no code execution beyond running the test suite. Phase 2 is a repeatable sprint template applied domain-by-domain — only the first sprint (engineering-team) is implemented here; subsequent sprints repeat the same steps.

**Tech Stack:** Python 3.11, pytest, GitHub Actions (existing `ci-quality-gate.yml`), standard markdown.

---

## Pre-Flight Check

Before starting any task, confirm the test suite currently passes:

```bash
cd /path/to/repo
pip install -r requirements-dev.txt
pytest tests/test_skill_integrity.py -v --tb=short 2>&1 | tail -20
```

Expected: all tests pass (or known failures are pre-existing — note them).

---

## Phase 1 — Standards Consolidation

---

### Task 1: Fix stale data in CONVENTIONS.md

**Files:**
- Modify: `CONVENTIONS.md`

Three stale items to fix before adding new content: the plugin.json version (says `2.1.2`, repo is `2.3.0`), the frontmatter rule (must allow the new optional `quality` field), and the skill counts in the domain table (says 35/30/43/28/14/13/6/4/2 — actuals from CLAUDE.md are 45/37/44/34/16/14/9/5/4).

- [ ] **Step 1: Fix plugin.json version**

In `CONVENTIONS.md`, find:
```
  "version": "2.1.2",
```
Replace with:
```
  "version": "2.3.0",
```

- [ ] **Step 2: Update frontmatter allowed fields**

In `CONVENTIONS.md`, find:
```
**Only two fields are allowed:**

```yaml
---
name: "skill-name"
description: "One-line description of when to use this skill. Be specific about trigger conditions."
---
```

**Do NOT include:** `license`, `metadata`, `triggers`, `version`, `author`, `category`, `updated`, or any other fields. PRs with extra frontmatter fields will be rejected.
```

Replace with:
```
**Allowed fields:**

```yaml
---
name: "skill-name"
description: "One-line description of when to use this skill. Be specific about trigger conditions."
quality: verified          # Optional — added after passing the quality audit
---
```

**Do NOT include:** `license`, `metadata`, `triggers`, `version`, `author`, `category`, `updated`, or any other fields. Only `name`, `description`, and optionally `quality` are accepted. PRs with other extra frontmatter fields will be rejected.
```

- [ ] **Step 3: Update domain table counts**

In `CONVENTIONS.md`, replace the entire domain table:
```
| Directory | Category | Current Count |
|-----------|----------|---------------|
| `engineering/` | POWERFUL-tier advanced engineering | 35 |
| `engineering-team/` | Core engineering roles | 30 |
| `marketing-skill/` | Marketing & growth | 43 |
| `c-level-advisor/` | Executive advisory | 28 |
| `product-team/` | Product management | 14 |
| `ra-qm-team/` | Regulatory & quality | 13 |
| `project-management/` | PM tools | 6 |
| `business-growth/` | Sales & business dev | 4 |
| `finance/` | Financial analysis | 2 |
```
With:
```
| Directory | Category | Current Count |
|-----------|----------|---------------|
| `engineering/` | POWERFUL-tier advanced engineering | 45 |
| `engineering-team/` | Core engineering roles | 37 |
| `marketing-skill/` | Marketing & growth | 44 |
| `c-level-advisor/` | Executive advisory | 34 |
| `product-team/` | Product management | 16 |
| `ra-qm-team/` | Regulatory & quality | 14 |
| `project-management/` | PM tools | 9 |
| `business-growth/` | Sales & business dev | 5 |
| `finance/` | Financial analysis | 4 |
```

- [ ] **Step 4: Update Quick Reference table**

In `CONVENTIONS.md`, find:
```
| Frontmatter fields | `name` + `description` only |
```
Replace with:
```
| Frontmatter fields | `name` + `description` required; `quality` optional |
```

Also find:
```
| Skill count | 205 (do not change) |
```
Replace with:
```
| Skill count | 235 (do not change without updating all count tables) |
```

- [ ] **Step 5: Commit**

```bash
git add CONVENTIONS.md
git commit -m "fix(conventions): update stale version, counts, and frontmatter rules"
```

---

### Task 2: Add quality rubric to CONVENTIONS.md

**Files:**
- Modify: `CONVENTIONS.md`

Add a new Section 11 (Quality Rubric) immediately before the existing "Quick Reference" section (which is after Section 10 Quality Validation).

- [ ] **Step 1: Locate insertion point**

In `CONVENTIONS.md`, find the line:
```
## Quick Reference
```

- [ ] **Step 2: Insert rubric section before Quick Reference**

Insert the following block immediately before `## Quick Reference`:

```markdown
---

## 11. Quality Rubric

Use this rubric when auditing existing skills or reviewing PRs. Score each dimension 1–5. Skills must score ≥ 3 on all five dimensions to receive `quality: verified`.

| Dimension | Poor (1) | Good (3) | Excellent (5) |
|-----------|----------|----------|---------------|
| **Actionability** | Vague advice, no steps | Steps with examples | Executable workflow the agent can run directly |
| **Depth** | Surface overview only | Core patterns covered | Edge cases + anti-patterns included |
| **Scripts** | None | 1 script with `--help` | 2+ scripts with `--help` and documented flags |
| **Cross-references** | None | 1–2 links to related skills | Full related-skill map with when/when-not context |
| **Freshness** | Stale or contradicted by newer skills | Mostly current | Actively maintained, no stale references |

**Passing threshold:** All dimensions ≥ 3.

**Audit outcomes:**
- **Keep** — all dimensions ≥ 3. Add `quality: verified` to frontmatter.
- **Deepen** — any dimension 1–2. File improvement tasks; re-score before marking verified.
- **Remove** — redundant, superseded, or unfixable. Delete skill, update domain index and docs.

**Audit record:** Every `quality: verified` tag must have a corresponding entry in `AUDIT_REPORT.md` before merging. PR reviewers enforce this gate.

---

```

- [ ] **Step 3: Commit**

```bash
git add CONVENTIONS.md
git commit -m "feat(conventions): add quality rubric section (5-dimension scoring)"
```

---

### Task 3: Add doc-counts consistency table to CONVENTIONS.md

**Files:**
- Modify: `CONVENTIONS.md`

When skill counts change, contributors must update multiple files. Add a lookup table so nothing gets missed.

- [ ] **Step 1: Locate insertion point**

In `CONVENTIONS.md`, find the existing Section 8 (Docs Site):

```
## 8. Docs Site
```

- [ ] **Step 2: Insert a new subsection at the end of Section 8**

After the paragraph "You do NOT need to create docs pages in your PR.", insert:

```markdown

### Count Consistency

When the skill count changes (new skill added or removed), update **all** of these files before merging:

| Field | Files to update |
|-------|----------------|
| Total skill count | `README.md` (badge + prose), `CLAUDE.md`, `CONVENTIONS.md` domain table, `docs/index.md` |
| Python tool count | `README.md`, `CLAUDE.md` |
| Agent count | `README.md`, `CLAUDE.md` |
| Command count | `README.md`, `CLAUDE.md` |
| GitHub star count | `README.md`, `CONTRIBUTING.md` (update only when meaningfully changed, e.g. per 500 stars) |

PRs that change skill counts without updating all listed files will be held until counts are aligned.
```

- [ ] **Step 3: Commit**

```bash
git add CONVENTIONS.md
git commit -m "feat(conventions): add count-consistency table for multi-file updates"
```

---

### Task 4: Archive SKILL-AUTHORING-STANDARD.md

**Files:**
- Modify: `SKILL-AUTHORING-STANDARD.md`

The 10-pattern authoring guide in SKILL-AUTHORING-STANDARD.md is valuable but conflicts with CONVENTIONS.md on frontmatter schema. The patterns themselves (Practitioner Voice, Multi-Mode, Proactive Triggers, etc.) are correct authoring guidance — they just need to live under CONVENTIONS.md's umbrella. Merge by reference: redirect the old file, append a Skill Authoring Patterns section to CONVENTIONS.md.

- [ ] **Step 1: Replace SKILL-AUTHORING-STANDARD.md body with redirect**

Overwrite `SKILL-AUTHORING-STANDARD.md` with:

```markdown
# Skill Authoring Standard

> **This document has been consolidated into [CONVENTIONS.md](CONVENTIONS.md).**
>
> See **Section 12 — Skill Authoring Patterns** in CONVENTIONS.md for the full authoring guide including the SKILL.md template, 10 patterns, and quality checklist.
>
> This file is kept for historical reference and link compatibility.
```

- [ ] **Step 2: Add Section 12 to CONVENTIONS.md**

In `CONVENTIONS.md`, find `## Quick Reference` and insert the following block immediately before it (after the rubric section added in Task 2):

```markdown
---

## 12. Skill Authoring Patterns

Detailed authoring guidance for writing high-quality skills. These patterns complement the structural rules in Sections 1–10.

### SKILL.md Template

```yaml
---
name: "skill-name"
description: "When to use this skill. Include trigger keywords. Mention related skills for disambiguation."
---
```

```markdown
# Skill Name

You are an expert in [domain]. Your goal is [specific outcome for the user].

## Before Starting

**Check for context first:**
If `[domain]-context.md` exists, read it before asking questions.

Gather this context (ask if not provided):
- **Current State:** What exists today? What's working / not working?
- **Goals:** What outcome do they want? What constraints exist?
- **[Domain-Specific]:** [Questions specific to this skill]

## How This Skill Works

### Mode 1: Build from Scratch
When starting fresh.

### Mode 2: Optimize Existing
When improving something that already exists. Analyze → identify gaps → recommend.

## [Core Workflow]

[Action-oriented. Tables for comparisons. Checklists for processes. Examples for clarity.]

## Proactive Triggers

Surface these without being asked:
- **[Condition]** → [What to flag and why]

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| [Common request] | [Specific deliverable with format] |

## Anti-Patterns

- ❌ [What NOT to do and why]

## Cross-References

- **[skill-name]**: Use when [scenario]. NOT for [disambiguation].

## Communication

All output: Bottom line first → What (with confidence) → Why → How to act.
Confidence tags: 🟢 verified / 🟡 medium / 🔴 assumed.
```
```

### The 10 Authoring Patterns

For the full 10-pattern guide (Context-First, Practitioner Voice, Multi-Mode, Related Skills, Reference Separation, Proactive Triggers, Output Artifacts, Quality Loop, Communication Standard, Python Tools), see the [SKILL-AUTHORING-STANDARD.md](SKILL-AUTHORING-STANDARD.md) archive — the detailed examples and rules remain valid, only the frontmatter schema section is superseded.

---

```

- [ ] **Step 3: Commit both files**

```bash
git add SKILL-AUTHORING-STANDARD.md CONVENTIONS.md
git commit -m "docs: consolidate SKILL-AUTHORING-STANDARD into CONVENTIONS.md (Section 12)"
```

---

### Task 5: Fix count and star discrepancies in README and CONTRIBUTING

**Files:**
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`

Key inconsistencies found:
- README says `5,200+` stars; CONTRIBUTING says `6,800+` stars
- README says `305` Python tools in two places; CLAUDE.md says `314`
- CONTRIBUTING says `205 production-ready skills`; everything else says `235`

- [ ] **Step 1: Fix README.md**

In `README.md`, find:
```
- **Python tools** — 305 CLI scripts (all stdlib-only, zero pip installs)
```
Replace with:
```
- **Python tools** — 314 CLI scripts (all stdlib-only, zero pip installs)
```

In `README.md`, find:
```
All 305 Python tools run anywhere Python runs.
```
Replace with:
```
All 314 Python tools run anywhere Python runs.
```

In `README.md`, find:
```
305 CLI tools ship with the skills (all verified, stdlib-only):
```
Replace with:
```
314 CLI tools ship with the skills (all verified, stdlib-only):
```

In `README.md`, find:
```
Yes. All 305 Python CLI tools use the standard library only
```
Replace with:
```
Yes. All 314 Python CLI tools use the standard library only
```

- [ ] **Step 2: Fix CONTRIBUTING.md**

In `CONTRIBUTING.md`, find:
```
Thank you for your interest in contributing! This repository is the largest open-source Claude Code skills & agent plugins library (6,800+ stars, 205 production-ready skills).
```
Replace with:
```
Thank you for your interest in contributing! This repository is the largest open-source Claude Code skills & agent plugins library (5,200+ stars, 235 production-ready skills).
```

- [ ] **Step 3: Commit**

```bash
git add README.md CONTRIBUTING.md
git commit -m "fix(docs): align skill count (235) and Python tool count (314) across all root docs"
```

---

### Task 6: Extend CI linter — description field + line count checks

**Files:**
- Modify: `tests/test_skill_integrity.py`
- Test: `tests/test_skill_integrity.py`

Currently `test_frontmatter_has_name` checks for `name:` but not `description:`. Also no line-count check exists. Add both. These are safe to make blocking — investigation shows 0 skills missing description and only 3 over 500 lines (which need fixing anyway).

**Note — required section names deliberately deferred:** The spec also calls for checking that Anti-Patterns and Cross-References sections exist. This is skipped here because section heading names vary widely across existing skills (`Related Skills`, `Cross-References`, `Resources`, etc.) — enforcing a specific heading name would fail on dozens of otherwise good skills. Phase 2 audit sprints normalize section names skill-by-skill. Once a domain is audited and verified, its skills will have canonical headings.

- [ ] **Step 1: Write failing tests first**

Run current tests to establish baseline:

```bash
pytest tests/test_skill_integrity.py::TestSkillMdFrontmatter -v --tb=short 2>&1 | tail -10
```

Expected: passes (description check doesn't exist yet — we're adding it).

- [ ] **Step 2: Add description check to TestSkillMdFrontmatter**

In `tests/test_skill_integrity.py`, find the end of the `TestSkillMdFrontmatter` class (after `test_frontmatter_has_name`). Add this method inside the class:

```python
    @pytest.mark.parametrize(
        "skill_dir",
        ALL_SKILL_DIRS,
        ids=[_short_id(s) for s in ALL_SKILL_DIRS],
    )
    def test_frontmatter_has_description(self, skill_dir):
        skill_md = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.match(r"^---\n(.*?)---\n", content, re.DOTALL)
        if match:
            fm = match.group(1)
            assert "description:" in fm, (
                f"{_short_id(skill_dir)}/SKILL.md frontmatter missing 'description' field"
            )
```

- [ ] **Step 3: Add a new TestSkillMdLineCount class**

After `TestSkillMdHasH1` and before `TestScriptDirectories`, insert:

```python
class TestSkillMdLineCount:
    """SKILL.md files must not exceed 500 lines."""

    @pytest.mark.parametrize(
        "skill_dir",
        ALL_SKILL_DIRS,
        ids=[_short_id(s) for s in ALL_SKILL_DIRS],
    )
    def test_under_500_lines(self, skill_dir):
        skill_md = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md, "r", encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) <= 500, (
            f"{_short_id(skill_dir)}/SKILL.md is {len(lines)} lines — exceeds 500-line limit. "
            "Move detailed content to references/ files."
        )
```

- [ ] **Step 4: Run tests — expect 3 failures on line count**

```bash
pytest tests/test_skill_integrity.py::TestSkillMdLineCount -v --tb=line 2>&1 | grep -E "FAILED|PASSED|ERROR" | head -20
```

Expected: 3 FAILED (the 3 skills already confirmed to exceed 500 lines). Note which skills they are from the output.

- [ ] **Step 5: Fix the 3 over-500-line skills**

For each failing skill, move the excess content to `references/` files. The general pattern:

1. Find the longest section (usually a large table, example catalog, or exhaustive reference list)
2. Create `references/<section-name>.md` containing that content
3. Replace the section in SKILL.md with a one-line reference:
   ```markdown
   > See [references/<section-name>.md](references/<section-name>.md) for the full catalog.
   ```
4. Verify line count drops below 500: `wc -l <skill>/SKILL.md`

- [ ] **Step 6: Re-run full test suite — all green**

```bash
pytest tests/test_skill_integrity.py -v --tb=short 2>&1 | tail -20
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add tests/test_skill_integrity.py
# Also add any SKILL.md and references/ files modified in Step 5
git add .
git commit -m "feat(tests): add description-field and 500-line limit checks to CI linter"
```

---

### Task 7: Extend CI linter — broken internal links check

**Files:**
- Modify: `tests/test_skill_integrity.py`
- Test: `tests/test_skill_integrity.py`

Skills reference `references/*.md` files inline. Currently nothing checks that those files exist. Add a check that resolves all markdown links pointing to `references/` within each SKILL.md.

- [ ] **Step 1: Add TestSkillMdInternalLinks class**

In `tests/test_skill_integrity.py`, after `TestSkillMdLineCount`, insert:

```python
class TestSkillMdInternalLinks:
    """Links to references/ files in SKILL.md must resolve to existing files."""

    @pytest.mark.parametrize(
        "skill_dir",
        ALL_SKILL_DIRS,
        ids=[_short_id(s) for s in ALL_SKILL_DIRS],
    )
    def test_references_links_resolve(self, skill_dir):
        skill_md = os.path.join(skill_dir, "SKILL.md")
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()

        # Find all markdown links: [text](path)
        links = re.findall(r"\[.*?\]\(([^)]+)\)", content)

        broken = []
        for link in links:
            # Only check relative links to references/ or assets/
            if link.startswith("http") or link.startswith("#"):
                continue
            if not (link.startswith("references/") or link.startswith("assets/")):
                continue
            target = os.path.join(skill_dir, link)
            if not os.path.exists(target):
                broken.append(link)

        assert not broken, (
            f"{_short_id(skill_dir)}/SKILL.md has broken internal links: {broken}"
        )
```

- [ ] **Step 2: Run the new check**

```bash
pytest tests/test_skill_integrity.py::TestSkillMdInternalLinks -v --tb=line 2>&1 | grep -E "FAILED|ERROR" | head -20
```

Expected: some failures for skills with broken references links. Note them.

- [ ] **Step 3: Fix any broken links found**

For each failing skill: either fix the link path in SKILL.md to point to the correct file, or create the missing references file if it genuinely should exist.

- [ ] **Step 4: Run full suite — all green**

```bash
pytest tests/test_skill_integrity.py -v --tb=short 2>&1 | tail -10
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add tests/test_skill_integrity.py
git commit -m "feat(tests): add broken-internal-links check to CI linter"
```

---

### Task 8: Add non-blocking extra-frontmatter audit report

**Files:**
- Modify: `tests/test_skill_integrity.py`

Investigation found 98 skills have extra frontmatter fields (`license`, `metadata`, etc.) inherited from the old SKILL-AUTHORING-STANDARD.md template. Blocking CI on all 98 now would break every PR touching those skills. Instead, add a non-blocking audit report test that prints a summary but does not fail. Phase 2 audit sprints will fix violations domain-by-domain; the report shrinks to zero over time. At that point, flip `WARN` to `FAIL`.

- [ ] **Step 1: Add TestFrontmatterExtraFieldsAudit class**

In `tests/test_skill_integrity.py`, after `TestSkillMdInternalLinks`, insert:

```python
class TestFrontmatterExtraFieldsAudit:
    """Report (but do not fail) skills with extra frontmatter fields.

    CONVENTIONS.md allows only: name, description, quality.
    Skills with legacy fields (license, metadata, version, author, category, updated)
    are tracked here. This test never fails — it prints a count report.
    Remove this class once all violations are fixed (Phase 2 audit complete).
    """

    ALLOWED_FIELDS = {"name", "description", "quality"}

    def test_report_extra_frontmatter_fields(self):
        violations = {}
        for skill_dir in ALL_SKILL_DIRS:
            skill_md = os.path.join(skill_dir, "SKILL.md")
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()

            match = re.match(r"^---\n(.*?)---\n", content, re.DOTALL)
            if not match:
                continue

            fm = match.group(1)
            fields = set(re.findall(r"^(\w[\w-]*):", fm, re.MULTILINE))
            extra = fields - self.ALLOWED_FIELDS
            if extra:
                violations[_short_id(skill_dir)] = sorted(extra)

        if violations:
            print(
                f"\n[AUDIT] {len(violations)} skills have extra frontmatter fields "
                f"(fix during Phase 2 domain audit sprints):"
            )
            for skill, fields in sorted(violations.items()):
                print(f"  {skill}: {fields}")

        # Never fail — this is a progress tracker, not a gate
        assert True
```

- [ ] **Step 2: Verify it runs and prints violations**

```bash
pytest tests/test_skill_integrity.py::TestFrontmatterExtraFieldsAudit -v -s 2>&1 | head -40
```

Expected: test PASSES, prints a list of ~98 skills with extra fields.

- [ ] **Step 3: Commit**

```bash
git add tests/test_skill_integrity.py
git commit -m "feat(tests): add non-blocking extra-frontmatter audit report (Phase 2 tracker)"
```

---

### Task 9: Phase 1 verification

**Files:** none (verification only)

- [ ] **Step 1: Run full test suite**

```bash
pytest tests/ -v --tb=short 2>&1 | tail -30
```

Expected: all tests pass. Note total test count.

- [ ] **Step 2: Verify CONVENTIONS.md is the single source of truth**

Check:
- `SKILL-AUTHORING-STANDARD.md` — should now be a redirect stub only
- `CONVENTIONS.md` — should contain Sections 1–12 + Quick Reference
- No other root-level files define frontmatter rules

```bash
grep -n "frontmatter\|YAML\|name:\|description:" CONVENTIONS.md | head -20
grep -rn "Only two fields\|license.*MIT\|metadata:" SKILL-AUTHORING-STANDARD.md
```

Expected: CONVENTIONS.md has the rules; SKILL-AUTHORING-STANDARD.md has only the redirect.

- [ ] **Step 3: Verify count consistency**

```bash
grep -n "235\|314\|5,200" README.md CONTRIBUTING.md CLAUDE.md | grep -v ".git"
```

Expected: 235 and 314 appear consistently; 5,200 only in README.md.

- [ ] **Step 4: Final commit if any loose ends**

```bash
git add -p  # Review and stage anything outstanding
git commit -m "chore: Phase 1 verification cleanup" || echo "Nothing to commit — clean"
```

---

## Phase 2 Sprint Template — Per-Domain Audit

**Important:** Run sprints sequentially. Complete one domain before starting the next. Freeze new skill PRs for a domain while its sprint is active.

**Sprint order:** engineering-team → engineering → product-team → marketing-skill → c-level-advisor → ra-qm-team → project-management → business-growth → finance

The following task is written for **Sprint 1: engineering-team**. For subsequent sprints, replace `engineering-team` with the next domain name throughout.

---

### Task 10: Sprint 1 — engineering-team audit setup

**Files:**
- Modify: `AUDIT_REPORT.md`

- [ ] **Step 1: Add sprint header to AUDIT_REPORT.md**

Append to `AUDIT_REPORT.md`:

```markdown
---

## Sprint 1 — engineering-team (2026-04-14)

**Skills in scope:** 37
**Freeze active:** Yes — no new engineering-team skill PRs during this sprint.

| Skill | Actionability | Depth | Scripts | Cross-refs | Freshness | Total | Outcome |
|-------|--------------|-------|---------|-----------|----------|-------|---------|
```

- [ ] **Step 2: Enumerate all skills in the domain**

```bash
ls /path/to/repo/engineering-team/ | grep -v "CLAUDE.md\|README.md\|SKILL.md\|START_HERE\|TEAM_STRUCTURE\|\.zip"
```

Add each skill as a row placeholder in the table (fill in scores next).

- [ ] **Step 3: Commit sprint setup**

```bash
git add AUDIT_REPORT.md
git commit -m "chore(audit): open Sprint 1 — engineering-team audit"
```

---

### Task 11: Sprint 1 — score each skill

**Files:**
- Modify: `AUDIT_REPORT.md`
- Modify: individual `SKILL.md` files (for Deepen outcomes)

For each skill in `engineering-team/`, open its SKILL.md and score it:

**Scoring process (per skill, ~3 minutes each):**

- [ ] Open `engineering-team/<skill>/SKILL.md`
- [ ] Score each dimension 1–5 using the rubric in CONVENTIONS.md Section 11
- [ ] Record scores in the AUDIT_REPORT.md sprint table
- [ ] Assign outcome: Keep / Deepen / Remove

**Outcome actions:**

*Keep (all ≥ 3):*
```yaml
# In the skill's SKILL.md frontmatter, add:
quality: verified
```

*Deepen (any dimension < 3):*

Create a GitHub issue or inline TODO comment listing specifically what's missing. Example for a skill scoring 2 on Scripts:
```markdown
<!-- AUDIT: needs a second script covering X use case — see Sprint 1 audit record -->
```
Fix the gap before marking verified. Re-score after fixing.

*Remove (redundant or unfixable):*
```bash
git rm -r engineering-team/<skill-name>/
# Update engineering-team/SKILL.md domain index to remove the skill
# Note in AUDIT_REPORT.md: "Removed — superseded by <other-skill>"
```

- [ ] **Step 4: Commit after each batch of 5 skills**

```bash
git add AUDIT_REPORT.md engineering-team/
git commit -m "audit(engineering-team): score skills <list names> — Sprint 1"
```

---

### Task 12: Sprint 1 — close and sync

**Files:**
- Modify: `AUDIT_REPORT.md`
- Modify: `README.md`, `CLAUDE.md` (if skill count changed)

- [ ] **Step 1: Mark sprint complete in AUDIT_REPORT.md**

Append to the Sprint 1 section:

```markdown
**Sprint 1 complete:** <date>
**Results:** X Keep / Y Deepen (fixed) / Z Remove
**Verified:** X skills tagged `quality: verified`
```

- [ ] **Step 2: Update skill counts if any skills were removed**

If Z > 0:
- Update `README.md` badge and prose skill count (235 − Z)
- Update `CLAUDE.md` engineering-team count (37 − Z)
- Update `CONVENTIONS.md` domain table

- [ ] **Step 3: Regenerate docs**

```bash
python3 scripts/generate-docs.py
```

Verify the engineering-team docs page reflects removed skills.

- [ ] **Step 4: Commit sprint close**

```bash
git add AUDIT_REPORT.md README.md CLAUDE.md CONVENTIONS.md docs/
git commit -m "audit(engineering-team): Sprint 1 complete — X verified, Z removed"
```

- [ ] **Step 5: Lift domain freeze**

Post in the PR description or a GitHub comment on any held PRs: "Sprint 1 engineering-team audit complete — PRs may now target this domain."

- [ ] **Step 6: Verify audit report test shrinks**

```bash
pytest tests/test_skill_integrity.py::TestFrontmatterExtraFieldsAudit -v -s 2>&1 | grep "\[AUDIT\]"
```

Expected: violation count has dropped by the number of engineering-team skills now tagged `quality: verified` (which have had their extra frontmatter fields cleaned up as part of Deepen fixes).

---

## Subsequent Sprints

Repeat Tasks 10–12 for each remaining domain in order:

| Sprint | Domain | Start task with |
|--------|--------|----------------|
| 2 | `engineering/` | Replace "engineering-team" with "engineering" |
| 3 | `product-team/` | Replace with "product-team" |
| 4 | `marketing-skill/` | Replace with "marketing-skill" |
| 5 | `c-level-advisor/` | Replace with "c-level-advisor" |
| 6 | `ra-qm-team/` | Replace with "ra-qm-team" |
| 7 | `project-management/` | Replace with "project-management" |
| 8 | `business-growth/` | Replace with "business-growth" |
| 9 | `finance/` | Replace with "finance" |

---

## Completion Gate

When all 9 sprints are done:

- [ ] `TestFrontmatterExtraFieldsAudit` violation count = 0
- [ ] Convert the audit report test from non-blocking to blocking:
  - In `test_report_extra_frontmatter_fields`, replace `assert True` with `assert not violations, f"Found {len(violations)} skills with extra frontmatter fields — all should be fixed by now."`
- [ ] Commit: `"feat(tests): promote extra-frontmatter check to blocking gate (Phase 2 complete)"`
