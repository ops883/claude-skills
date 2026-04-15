# Claude Code Skills & Plugins — Agent Skills for Every Coding Tool

**235 production-ready Claude Code skills, plugins, and agent skills for 12 AI coding tools.**

The most comprehensive open-source library of Claude Code skills and agent plugins — also works with OpenAI Codex, Gemini CLI, Cursor, and 7 more coding agents. Reusable expertise packages covering engineering, DevOps, marketing, compliance, C-level advisory, and more.

**Works with:** Claude Code · OpenAI Codex · Gemini CLI · OpenClaw · Hermes Agent · Cursor · Aider · Windsurf · Kilo Code · OpenCode · Augment · Antigravity

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Skills](https://img.shields.io/badge/Skills-235-brightgreen?style=for-the-badge)](#skills-overview)
[![Agents](https://img.shields.io/badge/Agents-28-blue?style=for-the-badge)](#agents)
[![Personas](https://img.shields.io/badge/Personas-3-purple?style=for-the-badge)](#personas)
[![Commands](https://img.shields.io/badge/Commands-27-orange?style=for-the-badge)](#commands)
[![Stars](https://img.shields.io/github/stars/alirezarezvani/claude-skills?style=for-the-badge)](https://github.com/alirezarezvani/claude-skills/stargazers)
[![SkillCheck Validated](https://img.shields.io/badge/SkillCheck-Validated-4c1?style=for-the-badge)](https://getskillcheck.com)

> **5,200+ GitHub stars** — the most comprehensive open-source Claude Code skills & agent plugins library.

---

## What Are Claude Code Skills & Agent Plugins?

Claude Code skills (also called agent skills or coding agent plugins) are modular instruction packages that give AI coding agents domain expertise they don't have out of the box. Each skill includes:

- **SKILL.md** — structured instructions, workflows, and decision frameworks
- **Python tools** — 314 CLI scripts (all stdlib-only, zero pip installs)
- **Reference docs** — templates, checklists, and domain-specific knowledge

**One repo, eleven platforms.** Works natively as Claude Code plugins, Codex agent skills, Gemini CLI skills, and converts to 8 more tools via `scripts/convert.sh`. All 314 Python tools run anywhere Python runs.

### Skills vs Agents vs Personas

| | Skills | Agents | Personas |
|---|---|---|---|
| **Purpose** | How to execute a task | What task to do | Who is thinking |
| **Scope** | Single domain | Single domain | Cross-domain |
| **Voice** | Neutral | Professional | Personality-driven |
| **Example** | "Follow these steps for SEO" | "Run a security audit" | "Think like a startup CTO" |

All three work together. See [Orchestration](#orchestration) for how to combine them.

---

## Quick Install

### Gemini CLI (New)

```bash
# Clone the repository
git clone https://github.com/alirezarezvani/claude-skills.git
cd claude-skills

# Run the setup script
./scripts/gemini-install.sh

# Start using skills
> activate_skill(name="senior-architect")
```

### Claude Code (Recommended)

```bash
# Add the marketplace
/plugin marketplace add alirezarezvani/claude-skills

# Install by domain
/plugin install engineering-skills@claude-code-skills          # 24 core engineering
/plugin install engineering-advanced-skills@claude-code-skills  # 25 POWERFUL-tier
/plugin install product-skills@claude-code-skills               # 12 product skills
/plugin install marketing-skills@claude-code-skills             # 43 marketing skills
/plugin install ra-qm-skills@claude-code-skills                 # 12 regulatory/quality
/plugin install pm-skills@claude-code-skills                    # 6 project management
/plugin install c-level-skills@claude-code-skills               # 28 C-level advisory (full C-suite)
/plugin install business-growth-skills@claude-code-skills       # 4 business & growth
/plugin install finance-skills@claude-code-skills               # 2 finance (analyst + SaaS metrics)

# Or install individual skills
/plugin install skill-security-auditor@claude-code-skills       # Security scanner
/plugin install playwright-pro@claude-code-skills                  # Playwright testing toolkit
/plugin install self-improving-agent@claude-code-skills         # Auto-memory curation
/plugin install content-creator@claude-code-skills              # Single skill
```

### OpenAI Codex

```bash
npx agent-skills-cli add alirezarezvani/claude-skills --agent codex
# Or: git clone + ./scripts/codex-install.sh
```

### OpenClaw

```bash
bash <(curl -s https://raw.githubusercontent.com/alirezarezvani/claude-skills/main/scripts/openclaw-install.sh)
```

### Manual Installation

```bash
git clone https://github.com/alirezarezvani/claude-skills.git
# Copy any skill folder to ~/.claude/skills/ (Claude Code) or ~/.codex/skills/ (Codex)
```

---

## Multi-Tool Support (New)

**Convert all 156 skills to 7 AI coding tools** with a single script:

| Tool | Format | Install |
|------|--------|---------|
| **Cursor** | `.mdc` rules | `./scripts/install.sh --tool cursor --target .` |
| **Aider** | `CONVENTIONS.md` | `./scripts/install.sh --tool aider --target .` |
| **Kilo Code** | `.kilocode/rules/` | `./scripts/install.sh --tool kilocode --target .` |
| **Windsurf** | `.windsurf/skills/` | `./scripts/install.sh --tool windsurf --target .` |
| **OpenCode** | `.opencode/skills/` | `./scripts/install.sh --tool opencode --target .` |
| **Augment** | `.augment/rules/` | `./scripts/install.sh --tool augment --target .` |
| **Antigravity** | `~/.gemini/antigravity/skills/` | `./scripts/install.sh --tool antigravity` |
| **Hermes Agent** | `~/.hermes/skills/` | `python scripts/sync-hermes-skills.py --verbose` |

**How it works:**

```bash
# 1. Convert all skills to all tools (takes ~15 seconds)
./scripts/convert.sh --tool all

# 2. Install into your project (with confirmation)
./scripts/install.sh --tool cursor --target /path/to/project

# Or use --force to skip confirmation:
./scripts/install.sh --tool aider --target . --force

# 3. Verify
find .cursor/rules -name "*.mdc" | wc -l  # Should show 156
```

**Each tool gets:**
- ✅ All 156 skills converted to native format
- ✅ Per-tool README with install/verify/update steps
- ✅ Support for scripts, references, templates where applicable
- ✅ Zero manual conversion work

Run `./scripts/convert.sh --tool all` to generate tool-specific outputs locally.

---

## Skills Overview

**235 skills across 9 domains:**

| Domain | Skills | Highlights | Details |
|--------|--------|------------|---------|
| **🔧 Engineering — Core** | 37 | Architecture, frontend, backend, fullstack, QA, DevOps, SecOps, AI/ML, data, Playwright, self-improving agent, security suite (6), a11y audit | [engineering-team/](engineering-team/) |
| **🎭 Playwright Pro** | 9+3 | Test generation, flaky fix, Cypress/Selenium migration, TestRail, BrowserStack, 55 templates | [engineering-team/playwright-pro](engineering-team/playwright-pro/) |
| **🧠 Self-Improving Agent** | 5+2 | Auto-memory curation, pattern promotion, skill extraction, memory health | [engineering-team/self-improving-agent](engineering-team/self-improving-agent/) |
| **⚡ Engineering — POWERFUL** | 45 | Agent designer, RAG architect, database designer, CI/CD builder, security auditor, MCP builder, AgentHub, Helm charts, Terraform, self-eval, llm-wiki (second brain for Obsidian), tc-tracker | [engineering/](engineering/) |
| **🎯 Product** | 16 | Product manager, agile PO, strategist, UX researcher, UI design, landing pages, SaaS scaffolder, analytics, experiment designer, discovery, roadmap communicator, code-to-prd, apple-hig-expert | [product-team/](product-team/) |
| **📣 Marketing** | 44 | 7 pods: Content (8), SEO (5), CRO (6), Channels (6), Growth (4), Intelligence (4), Sales (2) + context foundation + orchestration router. 32 Python tools. | [marketing-skill/](marketing-skill/) |
| **📋 Project Management** | 9 | Senior PM, scrum master, Jira, Confluence, Atlassian admin, templates | [project-management/](project-management/) |
| **🏥 Regulatory & QM** | 14 | ISO 13485, MDR 2017/745, FDA, ISO 27001, GDPR, CAPA, risk management | [ra-qm-team/](ra-qm-team/) |
| **💼 C-Level Advisory** | 34 | Full C-suite (10 roles) + orchestration + board meetings + culture & collaboration | [c-level-advisor/](c-level-advisor/) |
| **📈 Business & Growth** | 5 | Customer success, sales engineer, revenue ops, contracts & proposals | [business-growth/](business-growth/) |
| **💰 Finance** | 4 | Financial analyst (DCF, budgeting, forecasting), SaaS metrics coach (ARR, MRR, churn, LTV, CAC) | [finance/](finance/) |

<details>
<summary><strong>Full skills index — all 235 skills with one-line descriptions</strong></summary>

### Engineering Core (36)
| Skill | What it does |
|-------|-------------|
| `a11y-audit` | WCAG 2.2 accessibility audit — scan, fix, and verify with 2 Python tools |
| `adversarial-reviewer` | Adversarial code review through 3 hostile personas: Saboteur, New Hire, Security Auditor |
| `ai-security` | AI/ML system security — prompt injection, model inversion, data poisoning risk scoring |
| `aws-solution-architect` | AWS architecture design with serverless patterns, CDK, and IaC templates |
| `azure-cloud-architect` | Azure infrastructure design with ARM/Bicep templates and landing zones |
| `cloud-security` | Cloud infrastructure security — IAM privilege escalation, S3/SG misconfigurations |
| `code-reviewer` | Code review automation for TypeScript, JavaScript, Python, Go, Swift, Kotlin |
| `email-template-builder` | Production email templates in TSX (React Email) or MJML with 5 template types |
| `epic-design` | Cinematic 2.5D interactive websites — scroll storytelling, parallax, 45+ animation techniques |
| `gcp-cloud-architect` | GCP infrastructure design with Terraform modules and cloud-native patterns |
| `google-workspace-cli` | Google Workspace administration via the gws CLI |
| `incident-commander` | Incident command: SEV classification, OODA loops, comms templates, 6 Python tools |
| `incident-response` | Security incident triage, NIST SP 800-61 forensics, 14-type incident taxonomy |
| `ms365-tenant-manager` | Microsoft 365 tenant administration for Global Administrators |
| `playwright-pro` | Production-grade Playwright testing — generate, review, fix flaky tests, TestRail/BrowserStack |
| `red-team` | MITRE ATT&CK kill-chain planning, effort scoring, choke point identification |
| `security-pen-testing` | Penetration testing methodology, vulnerability assessment, exploit analysis |
| `self-improving-agent` | Curates Claude Code auto-memory — promotes patterns to CLAUDE.md, extracts reusable skills |
| `senior-architect` | System architecture design, microservices, distributed systems, ADRs |
| `senior-backend` | Backend APIs, microservices, database architecture, REST/GraphQL |
| `senior-computer-vision` | Object detection, image segmentation, visual AI pipeline engineering |
| `senior-data-engineer` | Scalable data pipelines, ETL/ELT, Spark, Airflow, data infrastructure |
| `senior-data-scientist` | Statistical modeling, experiment design, causal inference, ML workflows |
| `senior-devops` | CI/CD, infrastructure automation, containerization, cloud deployments |
| `senior-frontend` | React, Next.js, TypeScript, component architecture, performance |
| `senior-fullstack` | Full-stack scaffolding for Next.js/GraphQL/PostgreSQL and other modern stacks |
| `senior-ml-engineer` | ML model productionization, MLOps pipelines, LLM integrations |
| `senior-prompt-engineer` | Prompt optimization, RAG systems, multi-agent orchestration |
| `senior-qa` | Unit, integration, and E2E test generation with TDD workflows |
| `senior-secops` | Application security, vulnerability management, SAST/DAST, compliance |
| `senior-security` | Threat modeling, secure architecture, security code review |
| `snowflake-development` | Snowflake SQL, Dynamic Tables, Streams/Tasks, data pipeline optimization |
| `stripe-integration-expert` | Stripe subscriptions, webhooks, billing portal, usage-based pricing |
| `tdd-guide` | Test-driven development — red/green/refactor, fixture generation, 8 Python tools |
| `tech-stack-evaluator` | Technology comparison with weighted scoring, TCO analysis, migration estimates |
| `threat-detection` | Hypothesis-driven threat hunting, IOC sweeps, z-score anomaly detection |

### Engineering POWERFUL (46)
| Skill | What it does |
|-------|-------------|
| `agent-designer` | Multi-agent system design — architectures, tool boundaries, handoff protocols |
| `agent-workflow-designer` | Agent workflow patterns — routing, orchestration, state machines |
| `agenthub` | Spawns N parallel subagents competing on the same task, synthesizes best result |
| `api-design-reviewer` | REST/GraphQL API design review — consistency, versioning, backwards compatibility |
| `api-test-suite-builder` | Integration test suite generation for REST endpoints |
| `autoresearch-agent` | Autonomous experiment loop that optimizes any file by a measurable metric |
| `behuman` | Makes AI responses sound genuinely human — less robotic, more authentic |
| `browser-automation` | Browser task automation, web scraping, form filling, screenshot capture |
| `changelog-generator` | Structured changelog generation from git commit history |
| `ci-cd-pipeline-builder` | CI/CD pipeline construction for GitHub Actions, GitLab CI, CircleCI |
| `code-tour` | CodeTour walkthroughs — annotated guided tours of codebases |
| `codebase-onboarding` | Rapid codebase understanding — architecture maps, dependency graphs, entry points |
| `data-quality-auditor` | Dataset completeness, consistency, accuracy, and validity auditing |
| `database-designer` | Database schema design, migrations, query optimization |
| `database-schema-designer` | ERD diagrams, normalization, table relationships, index design |
| `demo-video` | Demo video scripts, product walkthroughs, feature showcase animations |
| `dependency-auditor` | Dependency security audits — CVEs, license conflicts, outdated packages |
| `docker-development` | Dockerfile optimization, docker-compose, multi-stage builds, container security |
| `env-secrets-manager` | Environment variable management, secrets rotation, .env best practices |
| `focused-fix` | Targeted fix mode — diagnose and repair a specific feature end-to-end |
| `git-worktree-manager` | Git worktree workflows for parallel feature development |
| `helm-chart-builder` | Helm chart development, templating, values hierarchy, chart testing |
| `interview-system-designer` | Technical interview process design, rubric creation, assessment structure |
| `karpathy-coder` | Enforces Karpathy's 4 coding principles in all code written |
| `llm-cost-optimizer` | LLM API cost reduction — token optimization, model routing, caching strategies |
| `llm-wiki` | Persistent personal knowledge base (Obsidian second brain) ingested by LLM |
| `mcp-server-builder` | MCP server construction — tools, resources, prompts, TypeScript/Python |
| `migration-architect` | Large-scale system migration planning — strangler fig, phased rollout |
| `monorepo-navigator` | Monorepo tooling (Nx, Turborepo), workspace configuration, build caching |
| `observability-designer` | Observability stack design — metrics, logs, traces, alerting |
| `performance-profiler` | Performance profiling, bottleneck identification, optimization strategies |
| `pr-review-expert` | Pull request review — security, logic, style, test coverage |
| `prompt-governance` | Production prompt management — versioning, A/B testing, drift detection |
| `rag-architect` | RAG pipeline design, retrieval strategies, embedding selection, chunking |
| `release-manager` | Release planning, changelogs, deployment coordination, rollback procedures |
| `runbook-generator` | Operational runbook generation for incidents and routine procedures |
| `secrets-vault-manager` | HashiCorp Vault, AWS Secrets Manager, Azure Key Vault integration |
| `self-eval` | Honest AI work quality evaluation with two-axis scoring |
| `skill-security-auditor` | Security audit of Claude Code skills for prompt injection and data leakage |
| `skill-tester` | Automated skill quality testing and benchmark evaluation |
| `spec-driven-workflow` | Spec-first development — acceptance criteria before code |
| `sql-database-assistant` | SQL query writing, optimization, migration generation |
| `statistical-analyst` | Hypothesis tests, A/B experiment analysis, sample size calculation |
| `tc-tracker` | Technical change lifecycle tracking with handoff format and 5 Python tools |
| `tech-debt-tracker` | Codebase tech debt scanning, severity scoring, prioritized backlog |
| `terraform-patterns` | Terraform module design, state management, security hardening, CI/CD |

### Product (16)
| Skill | What it does |
|-------|-------------|
| `agile-product-owner` | Agile backlog management, user story generation, sprint planning |
| `apple-hig-expert` | Apple HIG compliance — iOS/macOS/visionOS design audit with Liquid Glass focus |
| `code-to-prd` | Reverse-engineers any codebase into a Product Requirements Document |
| `competitive-teardown` | Competitor analysis, feature matrix, gap analysis, positioning |
| `experiment-designer` | A/B test planning, hypothesis writing, sample size calculation |
| `landing-page-generator` | High-converting landing pages as Next.js TSX + Tailwind CSS |
| `product-analytics` | KPI design, retention curves, cohort analysis, funnel conversion |
| `product-discovery` | Opportunity validation, assumption mapping, discovery sprints |
| `product-manager-toolkit` | RICE prioritization, customer interview analysis, 2 Python tools |
| `product-strategist` | OKR cascade generation, strategic planning frameworks |
| `research-summarizer` | Structured research synthesis for non-technical stakeholders |
| `roadmap-communicator` | Roadmap narratives, release notes, changelog generation |
| `saas-scaffolder` | Complete SaaS boilerplate with auth, billing, API setup |
| `spec-to-repo` | Converts a spec document into a scaffolded, runnable repository |
| `ui-design-system` | Design token generation, component systems, brand color cascades |
| `ux-researcher-designer` | Data-driven persona creation, user research synthesis |

### Marketing (44)
| Skill | What it does |
|-------|-------------|
| `ab-test-setup` | A/B test design, hypothesis writing, significance analysis |
| `ad-creative` | Ad creative generation and iteration for paid advertising |
| `ai-seo` | Optimize content for AI search citations (ChatGPT, Perplexity, Google AI Overviews) |
| `analytics-tracking` | GA4, Google Tag Manager, event tracking setup and audit |
| `app-store-optimization` | ASO keyword research, competitor analysis, listing optimization |
| `brand-guidelines` | Brand guideline application and enforcement |
| `campaign-analytics` | Multi-touch attribution, funnel conversion, campaign ROI with 3 Python tools |
| `churn-prevention` | Cancellation flow design, save offers, exit surveys, win-back sequences |
| `cold-email` | B2B cold outreach sequences that book meetings |
| `competitor-alternatives` | Competitor comparison and alternative pages for SEO |
| `content-creator` | Legacy redirect — routes to specialized content skills |
| `content-humanizer` | Makes AI-generated content sound genuinely human |
| `content-production` | Full content pipeline from topic to published-ready piece |
| `content-strategy` | Content strategy planning, topic clusters, editorial calendar |
| `copy-editing` | Marketing copy editing and improvement |
| `copywriting` | Marketing copy for landing pages, ads, emails, product pages |
| `email-sequence` | Drip campaigns, automated email sequences, lifecycle emails |
| `form-cro` | Lead gen and non-signup form optimization |
| `free-tool-strategy` | Free tool marketing strategy for lead gen and SEO |
| `launch-strategy` | Product launch planning, feature announcement, release strategy |
| `marketing-context` | Marketing context document that all marketing skills read before starting |
| `marketing-demand-acquisition` | Demand generation campaigns, paid ad optimization |
| `marketing-ideas` | Marketing strategy ideation for SaaS and software products |
| `marketing-ops` | Central router for the marketing skill ecosystem |
| `marketing-psychology` | Behavioral science principles applied to marketing copy and design |
| `marketing-strategy-pmm` | Product marketing positioning, GTM strategy, competitive intelligence |
| `onboarding-cro` | Post-signup onboarding optimization, activation, first-run experience |
| `page-cro` | Marketing page conversion optimization |
| `paid-ads` | Google Ads, Meta, LinkedIn paid advertising campaigns |
| `paywall-upgrade-cro` | In-app paywalls, upgrade screens, upsell modal optimization |
| `popup-cro` | Popup, modal, and overlay optimization |
| `pricing-strategy` | SaaS pricing design — tier structure, value metrics, pricing pages |
| `programmatic-seo` | SEO-driven pages at scale using templates and data |
| `prompt-engineer-toolkit` | AI prompt optimization and reusable prompt template libraries |
| `referral-program` | Referral and affiliate program design and optimization |
| `schema-markup` | Structured data implementation and validation |
| `seo-audit` | Technical SEO audit and diagnosis |
| `signup-flow-cro` | Signup, registration, and trial activation flow optimization |
| `site-architecture` | Website structure, URL hierarchy, internal linking strategy |
| `social-content` | LinkedIn, Twitter/X, and social media content creation |
| `social-media-analyzer` | Social media campaign analytics and performance tracking |
| `social-media-manager` | Social media strategy, content calendar, community management |
| `video-content-strategist` | Video content strategy, YouTube optimization, script writing |
| `x-twitter-growth` | X/Twitter audience building and viral content strategy |

### C-Level Advisory (28)
| Skill | What it does |
|-------|-------------|
| `agent-protocol` | Inter-agent communication protocol for C-suite agent teams |
| `board-deck-builder` | Board and investor update deck assembly from cross-functional inputs |
| `board-meeting` | Multi-agent board meeting protocol for strategic decisions |
| `ceo-advisor` | CEO strategic guidance — leadership, org design, board relations |
| `cfo-advisor` | CFO guidance — SaaS metrics, fundraising, financial planning |
| `change-management` | Organizational change rollout frameworks |
| `chief-of-staff` | C-suite orchestration and cross-functional coordination |
| `chro-advisor` | People leadership — hiring, performance, culture, compensation |
| `ciso-advisor` | Security leadership for growth-stage companies |
| `cmo-advisor` | Marketing leadership — demand gen, brand, PLG, pricing |
| `company-os` | Meta-framework for how a company runs — connective tissue across C-suite |
| `competitive-intel` | Systematic competitor tracking feeding CMO, CRO, and CPO workflows |
| `context-engine` | Loads and manages company context for all C-suite advisor skills |
| `coo-advisor` | Operations leadership — processes, metrics, scaling |
| `cpo-advisor` | Product leadership — roadmap, discovery, strategy |
| `cro-advisor` | Revenue leadership for B2B SaaS — pipeline, sales, success |
| `cs-onboard` | Founder onboarding interview capturing company context across 7 dimensions |
| `cto-advisor` | CTO guidance — architecture decisions, team building, technical strategy |
| `culture-architect` | Build and measure company culture as operational behavior |
| `decision-logger` | Two-layer memory architecture for board meeting decisions |
| `executive-mentor` | Adversarial thinking partner for founders and executives |
| `founder-coach` | Personal leadership development for founders and first-time CEOs |
| `internal-narrative` | One coherent company story across employees, investors, and customers |
| `intl-expansion` | International market expansion strategy |
| `ma-playbook` | M&A strategy for acquiring or being acquired |
| `org-health-diagnostic` | Cross-functional organizational health check |
| `scenario-war-room` | What-if modeling for cascading multi-variable scenarios |
| `strategic-alignment` | Cascades strategy from boardroom to individual contributor |

### Regulatory & QM (13)
| Skill | What it does |
|-------|-------------|
| `capa-officer` | CAPA system management for medical device QMS |
| `fda-consultant-specialist` | FDA regulatory guidance for medical device companies |
| `gdpr-dsgvo-expert` | GDPR and German DSGVO compliance automation |
| `information-security-manager-iso27001` | ISO 27001 ISMS implementation for HealthTech and MedTech |
| `isms-audit-expert` | ISO 27001 ISMS audit and compliance verification |
| `mdr-745-specialist` | EU MDR 2017/745 classification, technical documentation, notified body |
| `qms-audit-expert` | ISO 13485 internal audit for medical device QMS |
| `quality-documentation-manager` | Document control for medical device QMS |
| `quality-manager-qmr` | Senior QMR for HealthTech and MedTech companies |
| `quality-manager-qms-iso13485` | ISO 13485 QMS implementation and maintenance |
| `regulatory-affairs-head` | Senior RA Manager for HealthTech and MedTech companies |
| `risk-management-specialist` | ISO 14971 medical device risk management throughout product lifecycle |
| `soc2-compliance` | SOC 2 audit preparation, Trust Service Criteria mapping, controls |

### Project Management (8)
| Skill | What it does |
|-------|-------------|
| `atlassian-admin` | Atlassian platform administration — users, permissions, security |
| `atlassian-templates` | Jira and Confluence template creation and management |
| `confluence-expert` | Confluence spaces, knowledge bases, page templates, macros |
| `jira-expert` | Jira projects, JQL queries, automation rules, sprint management |
| `meeting-analyzer` | Meeting transcript analysis — behavioral patterns, action items |
| `scrum-master` | Data-driven Scrum coaching with velocity and retro frameworks |
| `senior-pm` | Enterprise project management — scope, risk, stakeholder comms |
| `team-communications` | Internal company communications — 3P updates, all-hands, announcements |

### Business & Growth (4)
| Skill | What it does |
|-------|-------------|
| `contract-and-proposal-writer` | Sales proposals, SOWs, and contract drafting |
| `customer-success-manager` | Customer health scoring, churn prediction, expansion opportunities |
| `revenue-operations` | Pipeline analysis, revenue forecasting, GTM efficiency metrics |
| `sales-engineer` | RFP gap analysis, competitive matrix, POC planning and execution |

### Finance (3)
| Skill | What it does |
|-------|-------------|
| `business-investment-advisor` | Business investment analysis and capital allocation |
| `financial-analyst` | DCF valuation, ratio analysis, budget variance, forecasting |
| `saas-metrics-coach` | SaaS financial health — ARR, MRR, churn, LTV, CAC, magic number |

</details>

---

## Personas

Pre-configured agent identities with curated skill loadouts, workflows, and distinct communication styles. Personas go beyond "use these skills" — they define how an agent thinks, prioritizes, and communicates.

| Persona | Domain | Best For |
|---------|--------|----------|
| [**Startup CTO**](agents/personas/startup-cto.md) | Engineering + Strategy | Architecture decisions, tech stack selection, team building, technical due diligence |
| [**Growth Marketer**](agents/personas/growth-marketer.md) | Marketing + Growth | Content-led growth, launch strategy, channel optimization, bootstrapped marketing |
| [**Solo Founder**](agents/personas/solo-founder.md) | Cross-domain | One-person startups, side projects, MVP building, wearing all hats |

**Usage:**
```bash
# Claude Code
cp agents/personas/startup-cto.md ~/.claude/agents/

# Any tool
./scripts/convert.sh --tool cursor  # Converts personas too
```

See [agents/personas/](agents/personas/) for details. Create your own with [TEMPLATE.md](agents/personas/TEMPLATE.md).

---

## Orchestration

A lightweight protocol for coordinating personas, skills, and agents on work that crosses domain boundaries. No framework required.

**Four patterns:**

| Pattern | What | When |
|---------|------|------|
| **Solo Sprint** | Switch personas across project phases | Side projects, MVPs, solo founders |
| **Domain Deep-Dive** | One persona + multiple stacked skills | Architecture reviews, compliance audits |
| **Multi-Agent Handoff** | Personas review each other's output | High-stakes decisions, launch readiness |
| **Skill Chain** | Sequential skills, no persona needed | Content pipelines, repeatable checklists |

**Example: 6-week product launch**
```
Week 1-2: startup-cto + aws-solution-architect + senior-frontend → Build
Week 3-4: growth-marketer + launch-strategy + copywriting + seo-audit → Prepare
Week 5-6: solo-founder + email-sequence + analytics-tracking → Ship and iterate
```

See [orchestration/ORCHESTRATION.md](orchestration/ORCHESTRATION.md) for the full protocol and examples.

---

## POWERFUL Tier

25 advanced skills with deep, production-grade capabilities:

| Skill | What It Does |
|-------|-------------|
| **agent-designer** | Multi-agent orchestration, tool schemas, performance evaluation |
| **agent-workflow-designer** | Sequential, parallel, router, orchestrator, and evaluator patterns |
| **rag-architect** | RAG pipeline builder, chunking optimizer, retrieval evaluator |
| **database-designer** | Schema analyzer, ERD generation, index optimizer, migration generator |
| **database-schema-designer** | Requirements → migrations, types, seed data, RLS policies |
| **migration-architect** | Migration planner, compatibility checker, rollback generator |
| **skill-security-auditor** | 🔒 Security gate — scan skills for malicious code before installation |
| **ci-cd-pipeline-builder** | Analyze stack → generate GitHub Actions / GitLab CI configs |
| **mcp-server-builder** | Build MCP servers from OpenAPI specs |
| **pr-review-expert** | Blast radius analysis, security scan, coverage delta |
| **api-design-reviewer** | REST API linter, breaking change detector, design scorecard |
| **api-test-suite-builder** | Scan API routes → generate complete test suites |
| **dependency-auditor** | Multi-language scanner, license compliance, upgrade planner |
| **release-manager** | Changelog generator, semantic version bumper, readiness checker |
| **observability-designer** | SLO designer, alert optimizer, dashboard generator |
| **performance-profiler** | Node/Python/Go profiling, bundle analysis, load testing |
| **monorepo-navigator** | Turborepo/Nx/pnpm workspace management & impact analysis |
| **changelog-generator** | Conventional commits → structured changelogs |
| **codebase-onboarding** | Auto-generate onboarding docs from codebase analysis |
| **runbook-generator** | Codebase → operational runbooks with commands |
| **git-worktree-manager** | Parallel dev with port isolation, env sync |
| **env-secrets-manager** | .env management, leak detection, rotation workflows |
| **incident-commander** | Incident response playbook, severity classifier, PIR generator |
| **tech-debt-tracker** | Codebase debt scanner, prioritizer, trend dashboard |
| **interview-system-designer** | Interview loop designer, question bank, calibrator |

---

## 🔒 Skill Security Auditor

New in v2.0.0 — audit any skill for security risks before installation:

```bash
python3 engineering/skill-security-auditor/scripts/skill_security_auditor.py /path/to/skill/
```

Scans for: command injection, code execution, data exfiltration, prompt injection, dependency supply chain risks, privilege escalation. Returns **PASS / WARN / FAIL** with remediation guidance.

**Zero dependencies.** Works anywhere Python runs.

---

## Recently Enhanced Skills

Production-quality upgrades added for:

- `engineering/git-worktree-manager` — worktree lifecycle + cleanup automation scripts
- `engineering/mcp-server-builder` — OpenAPI -> MCP scaffold + manifest validator
- `engineering/changelog-generator` — release note generator + conventional commit linter
- `engineering/ci-cd-pipeline-builder` — stack detector + pipeline generator
- `marketing-skill/prompt-engineer-toolkit` — prompt A/B tester + prompt version/diff manager

Each now ships with `scripts/`, extracted `references/`, and a usage-focused `README.md`.

---

## Usage Examples

### Architecture Review
```
Using the senior-architect skill, review our microservices architecture
and identify the top 3 scalability risks.
```

### Content Creation
```
Using the content-creator skill, write a blog post about AI-augmented
development. Optimize for SEO targeting "Claude Code tutorial".
```

### Compliance Audit
```
Using the mdr-745-specialist skill, review our technical documentation
for MDR Annex II compliance gaps.
```

---

## Python Analysis Tools

314 CLI tools ship with the skills (all verified, stdlib-only):

```bash
# SaaS health check
python3 finance/saas-metrics-coach/scripts/metrics_calculator.py --mrr 80000 --customers 200 --churned 3 --json

# Brand voice analysis
python3 marketing-skill/content-production/scripts/brand_voice_analyzer.py article.txt

# Tech debt scoring
python3 c-level-advisor/cto-advisor/scripts/tech_debt_analyzer.py /path/to/codebase

# RICE prioritization
python3 product-team/product-manager-toolkit/scripts/rice_prioritizer.py features.csv

# Security audit
python3 engineering/skill-security-auditor/scripts/skill_security_auditor.py /path/to/skill/

# Landing page (TSX + Tailwind)
python3 product-team/landing-page-generator/scripts/landing_page_scaffolder.py config.json --format tsx
```

---

## Related Projects

| Project | Description |
|---------|-------------|
| [**Claude Code Skills & Agents Factory**](https://github.com/alirezarezvani/claude-code-skills-agents-factory) | Methodology for building skills at scale |
| [**Claude Code Tresor**](https://github.com/alirezarezvani/claude-code-tresor) | Productivity toolkit with 60+ prompt templates |
| [**Product Manager Skills**](https://github.com/Digidai/product-manager-skills) | Senior PM agent with 6 knowledge domains, 12 templates, 30+ frameworks — discovery, strategy, delivery, SaaS metrics, career coaching, AI product craft |

---

## FAQ

**How do I install Claude Code plugins?**
Add the marketplace with `/plugin marketplace add alirezarezvani/claude-skills`, then install any skill bundle with `/plugin install <name>@claude-code-skills`.

**Do these skills work with OpenAI Codex / Cursor / Windsurf / Aider?**
Yes. Skills work natively with 12 tools: Claude Code, OpenAI Codex, Gemini CLI, OpenClaw, Hermes Agent, Cursor, Aider, Windsurf, Kilo Code, OpenCode, Augment, and Antigravity. Hermes Agent uses the same agentskills.io SKILL.md standard — run `python scripts/sync-hermes-skills.py` to install. For other tools run `./scripts/convert.sh --tool all` then `./scripts/install.sh --tool <name>`. See [Multi-Tool Integrations](https://alirezarezvani.github.io/claude-skills/integrations/) for details.

**Will updating break my installation?**
No. We follow semantic versioning and maintain backward compatibility within patch releases. Existing script arguments, plugin source paths, and SKILL.md structures are never changed in patch versions. See the [CHANGELOG](CHANGELOG.md) for details on each release.

**Are the Python tools dependency-free?**
Yes. All 314 Python CLI tools use the standard library only — zero pip installs required. Every script is verified to run with `--help`.

**How do I create my own Claude Code skill?**
Each skill is a folder with a `SKILL.md` (frontmatter + instructions), optional `scripts/`, `references/`, and `assets/`. See the [Skills & Agents Factory](https://github.com/alirezarezvani/claude-code-skills-agents-factory) for a step-by-step guide.

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick ideas:**
- Add new skills in underserved domains
- Improve existing Python tools
- Add test coverage for scripts
- Translate skills for non-English markets

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=alirezarezvani/claude-skills&type=Date)](https://star-history.com/#alirezarezvani/claude-skills&Date)

---

**Built by [Alireza Rezvani](https://alirezarezvani.com)** · [Medium](https://alirezarezvani.medium.com) · [Twitter](https://twitter.com/nginitycloud)
