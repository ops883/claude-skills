# Quality-First Roadmap — Design Spec

**Date:** 2026-04-14  
**Status:** Approved  
**Goal:** Improve quality over quantity across all 235 skills via a two-phase approach: standards consolidation first, then a rolling domain-by-domain audit.

---

## Context

The repository has grown to 235 skills across 9 domains with 314 Python tools, 28 agents, and 27 commands. Growth has been fast, but quality signals show cracks:

- Two conflicting standards documents (`SKILL-AUTHORING-STANDARD.md` vs `CONVENTIONS.md`) give contributors contradictory guidance
- Doc inconsistencies: star counts, skill counts, and Python tool counts differ between README, CONTRIBUTING.md, and CLAUDE.md
- Test coverage is thin — 13 test files for 235 skills and 314 scripts
- No systematic quality scoring or audit history exists
- `eval-workspace/` contains only `iteration-1` — quality evaluation is not systematized

**Decision:** Prioritized roadmap, quality over quantity. Two phases: fix the standards layer first, then use those standards to audit existing content on a rolling basis.

---

## Phase 1 — Standards Consolidation

**Goal:** Single source of truth for what "quality" means. Tighten the CI gate. Fix doc inconsistencies.

### 1.1 Merge Standards Documents

Merge `SKILL-AUTHORING-STANDARD.md` into `CONVENTIONS.md` as the single canonical standard. Replace the body of `SKILL-AUTHORING-STANDARD.md` with a one-line redirect to `CONVENTIONS.md`.

**What moves into CONVENTIONS.md:**
- Full SKILL.md template (from SKILL-AUTHORING-STANDARD.md)
- Mode patterns (Build from Scratch, Optimize Existing, Situation-Specific)
- Proactive Triggers section requirement
- Output Artifacts table requirement
- Communication standards reference

**What stays as-is in CONVENTIONS.md:**
- Domain table and placement rules
- Script conventions (stdlib-only, `--help` required)
- Git/PR workflow rules

**What changes in CONVENTIONS.md:**
- Frontmatter schema expands to allow one optional field: `quality: verified`. All other extra fields remain forbidden. The CI linter is updated to reflect this (allow `name`, `description`, and optionally `quality`).

### 1.2 Quality Rubric

Add a **5-dimension scoring table** to `CONVENTIONS.md`. Used by both human reviewers and the rolling audit (Phase 2).

| Dimension | Poor (1) | Good (3) | Excellent (5) |
|-----------|----------|----------|---------------|
| **Actionability** | Vague advice, no steps | Steps with examples | Executable workflow, agent can run it |
| **Depth** | Surface overview only | Core patterns covered | Edge cases + anti-patterns included |
| **Scripts** | None | 1 basic script with `--help` | 2+ scripts with `--help` and documented flags |
| **Cross-references** | None | 1–2 links to related skills | Full related-skill map with context |
| **Freshness** | Stale or contradicted by newer skills | Mostly current | Actively maintained, no stale references |

**Passing threshold:** Score ≥ 3 on all five dimensions. Skills below threshold are flagged for deepening or removal.

### 1.3 CI Linter Extension

Extend `tests/test_skill_integrity.py` to enforce:

| Check | Rule |
|-------|------|
| Frontmatter fields | Exactly `name` and `description` — no extras, none missing |
| Required sections | Title (H1), Overview, Core Content, Anti-Patterns, Cross-References |
| Line count | ≤ 500 lines per SKILL.md |
| Internal links | All `references/` links in SKILL.md resolve to existing files |
| Script `--help` | All `.py` files in `scripts/` respond to `--help` without error |

These checks run on every PR via the existing `ci-quality-gate.yml` workflow.

### 1.4 Doc Consistency Fix

Audit and align the following numbers across all root-level docs:

| Field | Files to update |
|-------|----------------|
| GitHub star count | README.md, CONTRIBUTING.md |
| Total skill count | README.md, CLAUDE.md, CONVENTIONS.md, docs/index.md |
| Python tool count | README.md, CLAUDE.md |
| Agent count | README.md, CLAUDE.md |
| Command count | README.md, CLAUDE.md |

Add a note in `CONVENTIONS.md`: "When changing skill counts, update all files listed in this table before merging."

### Phase 1 Deliverables

- [ ] `CONVENTIONS.md` updated with merged template + quality rubric + consistency table
- [ ] `SKILL-AUTHORING-STANDARD.md` replaced with redirect
- [ ] `tests/test_skill_integrity.py` extended with new checks
- [ ] All doc count inconsistencies resolved

---

## Phase 2 — Rolling Domain Audit

**Goal:** Score every existing skill against the Phase 1 rubric. Keep, deepen, or remove. One domain per sprint.

### Audit Order

Domains are prioritized by user-facing impact — most installed/referenced first:

| Sprint | Domain | Skill Count | Rationale |
|--------|--------|-------------|-----------|
| 1 | `engineering-team/` | 37 | Highest-traffic, most downloaded |
| 2 | `engineering/` | 45 | POWERFUL-tier — sets quality bar for the whole repo |
| 3 | `product-team/` | 16 | Small, high-visibility, frequently referenced |
| 4 | `marketing-skill/` | 44 | Large domain, mixed quality signals |
| 5 | `c-level-advisor/` | 34 | High-stakes content, needs accuracy |
| 6 | `ra-qm-team/` | 14 | Compliance — correctness is critical |
| 7 | `project-management/` | 9 | Small, lower traffic |
| 8 | `business-growth/` | 5 | Small |
| 9 | `finance/` | 4 | Small |

### Per-Skill Audit Process

For each skill in the sprint domain:

1. Score against the 5-dimension rubric (1–5 per dimension)
2. Assign one of three outcomes:

| Outcome | Condition | Action |
|---------|-----------|--------|
| **Keep** | All dimensions ≥ 3 | Add `quality: verified` to frontmatter |
| **Deepen** | Any dimension scores 1–2 | File specific improvement tasks, fix before marking verified |
| **Remove** | Redundant, superseded, or unfixable | Delete skill, update domain SKILL.md and docs |

3. Record in `AUDIT_REPORT.md`: skill name, scores per dimension, outcome, sprint, date

### `quality: verified` Tag

Skills that pass the rubric receive a frontmatter tag:

```yaml
---
name: "skill-name"
description: "..."
quality: verified
---
```

CI enforces: a PR adding `quality: verified` must include an `AUDIT_REPORT.md` entry with scores for that skill. Tags added without audit records are rejected.

### Domain Freeze Rule

While a domain's audit sprint is in progress, new skill additions to that domain are frozen. PRs adding skills to a domain under active audit are held until the sprint closes. This prevents the audit target from moving.

### Phase 2 Deliverables (per sprint)

- [ ] All skills in domain scored in `AUDIT_REPORT.md`
- [ ] "Deepen" skills improved or removed
- [ ] "Keep" skills tagged `quality: verified`
- [ ] Domain `SKILL.md` index updated to reflect removals
- [ ] MkDocs docs regenerated for domain

---

## What This Design Explicitly Excludes

- **No new skills during Phase 1.** Focus is on standards, not content.
- **No platform integration changes.** Cross-tool sync (Codex, Gemini) is out of scope.
- **No skill count targets.** Quality improvement may reduce the total count — that's acceptable.
- **No external tooling.** Everything runs in the existing Python + GitHub Actions stack.

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Standards docs | 1 canonical doc (CONVENTIONS.md), 0 conflicts |
| CI linter checks | All 5 new checks passing on every PR |
| Doc consistency | 0 count mismatches across root-level docs |
| Audit coverage | 100% of skills scored by end of Phase 2 |
| Quality pass rate | ≥ 75% of skills reach `quality: verified` |
| Removal rate | Expected 10–20% of skills removed or merged |
