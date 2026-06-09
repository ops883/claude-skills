# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This is a **comprehensive skills library** for Claude AI and Claude Code - reusable, production-ready skill packages that bundle domain expertise, best practices, analysis tools, and strategic frameworks. The repository provides modular skills that teams can download and use directly in their workflows.

**Current Scope:** ~235 production-ready skills across 9 domains with 320+ Python automation tools, 440+ reference guides, 28 agents, and 29 slash commands. Also distributed as 6 ChatGPT Custom GPTs (`custom-gpt/`) and synced to 12 supported agent tools.

**Key Distinction**: This is NOT a traditional application. It's a library of skill packages meant to be extracted and deployed by users into their own Claude workflows.

## Navigation Map

This repository uses **modular documentation**. For domain-specific guidance, see:

| Domain | CLAUDE.md Location | Focus |
|--------|-------------------|-------|
| **Agent Development** | [agents/CLAUDE.md](agents/CLAUDE.md) | cs-* agent creation, YAML frontmatter, relative paths |
| **Marketing Skills** | [marketing-skill/CLAUDE.md](marketing-skill/CLAUDE.md) | Content creation, SEO, ASO, demand gen, campaign analytics |
| **Product Team** | [product-team/CLAUDE.md](product-team/CLAUDE.md) | RICE, OKRs, user stories, UX research, SaaS scaffolding |
| **Engineering (Core)** | [engineering-team/CLAUDE.md](engineering-team/CLAUDE.md) | Fullstack, AI/ML, DevOps, security, data, QA tools |
| **Engineering (POWERFUL)** | [engineering/](engineering/) | Agent design, RAG, MCP, CI/CD, database, observability |
| **C-Level Advisory** | [c-level-advisor/CLAUDE.md](c-level-advisor/CLAUDE.md) | CEO/CTO strategic decision-making |
| **Project Management** | [project-management/CLAUDE.md](project-management/CLAUDE.md) | Atlassian MCP, Jira/Confluence integration |
| **RA/QM Compliance** | [ra-qm-team/CLAUDE.md](ra-qm-team/CLAUDE.md) | ISO 13485, MDR, FDA, GDPR, ISO 27001 compliance |
| **Business & Growth** | [business-growth/CLAUDE.md](business-growth/CLAUDE.md) | Customer success, sales engineering, revenue operations |
| **Finance** | [finance/CLAUDE.md](finance/CLAUDE.md) | Financial analysis, DCF valuation, budgeting, forecasting, SaaS metrics |
| **Standards Library** | [standards/CLAUDE.md](standards/CLAUDE.md) | Communication, quality, git, security standards |
| **Templates** | [templates/CLAUDE.md](templates/CLAUDE.md) | Template system usage |

## Architecture Overview

### Repository Structure

```
claude-code-skills/
├── .claude-plugin/            # Plugin registry (marketplace.json)
├── agents/                    # 25 agents across all domains
├── commands/                  # 29 slash commands (changelog, tdd, saas-health, prd, code-to-prd, plugin-audit, sprint-plan, wiki-*, tc, etc.)
├── engineering-team/          # 37 core engineering skills + Playwright Pro + Self-Improving Agent + Security Suite
├── engineering/               # 47 POWERFUL-tier advanced skills (incl. AgentHub, self-eval, llm-wiki, tc-tracker, karpathy-coder)
├── product-team/              # 17 product skills (incl. apple-hig-expert) + Python tools
├── marketing-skill/           # 45 marketing skills (7 pods) + Python tools
├── c-level-advisor/           # 34 C-level advisory skills (10 roles + orchestration)
├── project-management/        # 9 PM skills + Atlassian MCP
├── ra-qm-team/                # 14 RA/QM compliance skills
├── business-growth/           # 5 business & growth skills + Python tools
├── finance/                   # 4 finance skills + Python tools
├── custom-gpt/                # 6 Custom GPTs (ChatGPT distribution of the skills library)
├── orchestration/            # Orchestration Protocol — persona + skill + task-agent coordination pattern
├── eval-workspace/            # Skill evaluation results (Tessl)
├── standards/                 # 5 standards library files
├── templates/                 # Reusable templates
├── tests/                     # pytest suite for selected Python tools (12 test modules)
├── docs/                      # MkDocs Material documentation site
├── scripts/                   # Build/sync scripts (docs generation, cross-tool sync incl. Hermes)
└── documentation/             # Implementation plans, sprints, delivery
```

### Root-Level Governance Docs

| File | Purpose |
|------|---------|
| [CONVENTIONS.md](CONVENTIONS.md) | **Mandatory** conventions for all contributors (human + AI). Skill structure, domains, naming, the **Quality Rubric** (5-dimension 1–5 scoring; ≥3 on all dims for `quality: verified`). |
| [SKILL-AUTHORING-STANDARD.md](SKILL-AUTHORING-STANDARD.md) | How to author a compliant SKILL.md (frontmatter, structure). |
| [SKILL_PIPELINE.md](SKILL_PIPELINE.md) | The skill creation → audit → publish pipeline. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution workflow and PR process. |
| [STORE.md](STORE.md) / [INSTALLATION.md](INSTALLATION.md) | Distribution and install instructions. |
| [GEMINI.md](GEMINI.md) | Gemini CLI cross-tool guidance. |

### Skill Package Pattern

Each skill follows this structure:
```
skill-name/
├── SKILL.md              # Master documentation
├── scripts/              # Python CLI tools (no ML/LLM calls)
├── references/           # Expert knowledge bases
└── assets/               # User templates
```

**Design Philosophy**: Skills are self-contained packages. Each includes executable tools (Python scripts), knowledge bases (markdown references), and user-facing templates. Teams can extract a skill folder and use it immediately.

**Key Pattern**: Knowledge flows from `references/` → into `SKILL.md` workflows → executed via `scripts/` → applied using `assets/` templates.

## Git Workflow

**Branch Strategy:** feature → dev → main (PR only)

**Branch Protection Active:** Main branch requires PR approval. Direct pushes blocked.

### Quick Start

```bash
# 1. Always start from dev
git checkout dev
git pull origin dev

# 2. Create feature branch
git checkout -b feature/agents-{name}

# 3. Work and commit (conventional commits)
feat(agents): implement cs-{agent-name}
fix(tool): correct calculation logic
docs(workflow): update branch strategy

# 4. Push and create PR to dev
git push origin feature/agents-{name}
gh pr create --base dev --head feature/agents-{name}

# 5. After approval, PR merges to dev
# 6. Periodically, dev merges to main via PR
```

**Branch Protection Rules:**
- ✅ Main: Requires PR approval, no direct push
- ✅ Dev: Unprotected, but PRs recommended
- ✅ All: Conventional commits enforced

See [documentation/WORKFLOW.md](documentation/WORKFLOW.md) for complete workflow guide.
See [standards/git/git-workflow-standards.md](standards/git/git-workflow-standards.md) for commit standards.

## Development Environment

**No application build system** - intentional design choice for portability. Skills are extracted and run as-is.

**Python Scripts:**
- Use standard library only (minimal dependencies)
- CLI-first design for easy automation
- Support both JSON and human-readable output
- No ML/LLM calls (keeps skills portable and fast)
- Every script must respond to `--help`

**Testing:**
- A lightweight `tests/` directory holds a **pytest** suite (12 modules) covering selected Python tools (e.g. `test_dcf_valuation.py`, `test_okr_tracker.py`, `test_commit_linter.py`, `test_gdpr_compliance.py`).
- Run with `pytest` from the repo root. Tests are stdlib + pytest only — no other infra.
- This is a smoke/regression net for tools, not a full app test framework. Skills themselves remain self-contained.

**If adding dependencies:**
- Keep scripts runnable with minimal setup (`pip install package` at most)
- Document all dependencies in SKILL.md
- Prefer standard library implementations

**Cross-Tool Sync:** `scripts/` contains sync utilities (e.g. `sync-hermes-skills.py`) that mirror skills to other agent tools. The library targets **12 supported tools**: Claude Code, OpenAI Codex, Cursor, Gemini CLI, Antigravity, OpenCode, OpenClaw, Hermes Agent, and others.

## Current Version

**Version:** v2.3.0 (latest)

**v2.3.0 Highlights:**
- **karpathy-coder** — new engineering skill: active coding-discipline enforcer (Karpathy's "keep the LLM on a tight leash" pattern). Passes the 8-phase plugin audit and wires into repo integration.
- **Hermes Agent** promoted as the **12th supported cross-tool** across all docs, with a `scripts/sync-hermes-skills.py` sync script.
- **Quality Rubric** added to [CONVENTIONS.md](CONVENTIONS.md) — a 5-dimension (1–5) scoring system; skills must score ≥3 on all five to earn `quality: verified`.
- **llm-wiki plugin** — POWERFUL-tier skill implementing Karpathy's LLM Wiki pattern. Second brain for Claude Code + Obsidian where the LLM incrementally ingests sources into a persistent, interlinked markdown vault. Ships SKILL.md (with `context: fork`), 3 sub-agents (wiki-ingestor, wiki-librarian, wiki-linter), 5 slash commands (/wiki-init, /wiki-ingest, /wiki-query, /wiki-lint, /wiki-log), 8 stdlib-only Python tools, 8 reference guides, full vault templates, and a worked example.
- **tc-tracker** — engineering skill: task context tracker with lifecycle, handoff format, schema, and 5 Python tools (tc_init, tc_create, tc_update, tc_status, tc_validator) plus `/tc` slash command
- **apple-hig-expert** — product skill: Apple Human Interface Guidelines expert with Liquid Glass aesthetic focus. Audits iOS/macOS/visionOS apps with `hig_checker` Python tool and comprehensive reference docs on visual design, platform specifics, and accessibility
- **custom-gpt/** and **orchestration/** — 6 ChatGPT Custom GPTs packaging the library, plus the dependency-free Orchestration Protocol for coordinating personas, skills, and task agents.
- ~235 skills across 9 domains, 320+ Python tools, 440+ references, 28 agents, 29 commands, 12 supported tools

> **Note on counts:** headline figures vary slightly with counting method (some skills nest example `SKILL.md` files under `references/`/`assets/`). The canonical per-domain counts live in [CONVENTIONS.md](CONVENTIONS.md); treat the numbers here as approximate and verify with `find <domain> -maxdepth 2 -name SKILL.md` when precision matters.

**Version:** v2.2.0

**v2.2.0 Highlights:**
- **Security skills suite** — 6 new engineering-team skills: adversarial-reviewer, ai-security, cloud-security, incident-response, red-team, threat-detection (5 Python tools, 4 reference guides)
- **Self-eval skill** — Honest AI work quality evaluation with two-axis scoring, score inflation detection, and session persistence
- **Snowflake development** — Data warehouse development, SQL optimization, and data pipeline patterns
- 234 total skills across 9 domains, 306 Python tools, 427 references, 25 agents, 22 commands
- MkDocs docs site expanded to 269 generated pages (301 HTML pages)

**v2.1.2 (2026-03-10):**
- Landing page generator now outputs **Next.js TSX + Tailwind CSS** by default (4 design styles, 7 section generators)
- **Brand voice integration** — landing page workflow uses marketing brand voice analyzer to match copy tone to design style
- 25 Python scripts fixed across all domains (syntax, dependencies, argparse)
- 237/237 scripts verified passing `--help`

**v2.1.1 (2026-03-07):**
- 18 skills optimized from 66-83% to 85-100% via Tessl quality review
- YAML frontmatter (name + description) added to all SKILL.md files
- 6 new agents + 5 slash commands, Gemini CLI support, MkDocs docs site

**v2.0.0 (2026-02-16):**
- 25 POWERFUL-tier engineering skills added (engineering/ folder)
- Plugin marketplace infrastructure (.claude-plugin/marketplace.json)
- Multi-platform support: Claude Code, OpenAI Codex, OpenClaw, Hermes Agent, Gemini CLI, Cursor, and 6 more

**Past Sprints:** See [documentation/delivery/](documentation/delivery/) and [CHANGELOG.md](CHANGELOG.md) for history.

## Roadmap

**Phase 1-3 Complete:** ~235 production-ready skills deployed across 9 domains
- Engineering Core (37), Engineering POWERFUL (47), Product (17), Marketing (45), PM (9), C-Level (34), RA/QM (14), Business & Growth (5), Finance (4)
- 320+ Python automation tools, 440+ reference guides, 28 agents, 29 commands
- Complete enterprise coverage from engineering through regulatory compliance, sales, customer success, and finance
- MkDocs Material docs site for SEO; distributed via ClawHub registry, the plugin marketplace, and 6 ChatGPT Custom GPTs

See domain-specific roadmaps in each skill folder's README.md or roadmap files.

## Key Principles

1. **Skills are products** - Each skill deployable as standalone package
2. **Documentation-driven** - Success depends on clear, actionable docs
3. **Algorithm over AI** - Use deterministic analysis (code) vs LLM calls
4. **Template-heavy** - Provide ready-to-use templates users customize
5. **Platform-specific** - Specific best practices > generic advice

## ClawHub Publishing Constraints

This repository publishes skills to **ClawHub** (clawhub.com) as the distribution registry. The following rules are **non-negotiable**:

1. **cs- prefix for slug conflicts only.** When a skill slug is already taken on ClawHub by another publisher, publish with the `cs-` prefix (e.g., `cs-copywriting`, `cs-seo-audit`). The `cs-` prefix applies **only on the ClawHub registry** — repo folder names, local skill names, and all other tools (Claude Code, Codex, Gemini CLI) remain unchanged.
2. **Never rename repo folders or local skill names** to match ClawHub slugs. The repo is the source of truth.
3. **No paid/commercial service dependencies.** Skills must not require paid third-party API keys or commercial services unless provided by the project itself. Free-tier APIs and BYOK (bring-your-own-key) patterns are acceptable.
4. **Rate limit: 5 new skills per hour** on ClawHub. Batch publishes must respect this. Use the drip timer (`clawhub-drip.timer`) for bulk operations.
5. **plugin.json schema** — ONLY these fields: `name`, `description`, `version`, `author`, `homepage`, `repository`, `license`, `skills: "./"`. No extra fields.
6. **Version follows repo versioning.** ClawHub package versions must match the repo release version (currently v2.2.0+).

## Anti-Patterns to Avoid

- Creating dependencies between skills (keep each self-contained)
- Adding complex build systems or heavy test infra (the `tests/` suite is intentionally lightweight pytest only — keep it that way)
- Generic advice (focus on specific, actionable frameworks)
- LLM calls in scripts (defeats portability and speed)
- Over-documenting file structure (skills are simple by design)

## Working with This Repository

**Creating New Skills:** Follow the appropriate domain's roadmap and CLAUDE.md guide (see Navigation Map above).

**Editing Existing Skills:** Maintain consistency across markdown files. Use the same voice, formatting, and structure patterns.

**Quality Standard:** Each skill should save users 40%+ time while improving consistency/quality by 30%+. Audit against the **Quality Rubric** in [CONVENTIONS.md](CONVENTIONS.md) (score ≥3 on all 5 dimensions for `quality: verified`). The `/plugin-audit` skill runs the full 8-phase audit pipeline on a skill directory.

## Additional Resources

- **.gitignore:** Excludes .vscode/, .DS_Store, AGENTS.md, PROMPTS.md, .env*
- **Conventions:** [CONVENTIONS.md](CONVENTIONS.md) - Mandatory rules + Quality Rubric (read before authoring/editing skills)
- **Skill Authoring:** [SKILL-AUTHORING-STANDARD.md](SKILL-AUTHORING-STANDARD.md), [SKILL_PIPELINE.md](SKILL_PIPELINE.md)
- **Plugin Registry:** [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) - Marketplace distribution
- **Standards Library:** [standards/](standards/) - Communication, quality, git, documentation, security
- **Implementation Plans:** [documentation/implementation/](documentation/implementation/)
- **Sprint Delivery:** [documentation/delivery/](documentation/delivery/)

---

**Last Updated:** June 9, 2026
**Version:** v2.3.0
**Status:** ~235 skills deployed across 9 domains, 35 marketplace plugins, 12 supported tools, docs site live
