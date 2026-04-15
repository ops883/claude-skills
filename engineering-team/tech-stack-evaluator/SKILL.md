---
name: "tech-stack-evaluator"
description: Technology stack evaluation and comparison with TCO analysis, security assessment, and ecosystem health scoring. Use when comparing frameworks, evaluating technology stacks, calculating total cost of ownership, assessing migration paths, or analyzing ecosystem viability.
---

# Technology Stack Evaluator

Evaluate and compare technologies, frameworks, and cloud providers with data-driven analysis and actionable recommendations.

## Table of Contents

- [Capabilities](#capabilities)
- [Quick Start](#quick-start)
- [Input Formats](#input-formats)
- [Analysis Types](#analysis-types)
- [Scripts](#scripts)
- [References](#references)

---

## Capabilities

| Capability | Description |
|------------|-------------|
| Technology Comparison | Compare frameworks and libraries with weighted scoring |
| TCO Analysis | Calculate 5-year total cost including hidden costs |
| Ecosystem Health | Assess GitHub metrics, npm adoption, community strength |
| Security Assessment | Evaluate vulnerabilities and compliance readiness |
| Migration Analysis | Estimate effort, risks, and timeline for migrations |
| Cloud Comparison | Compare AWS, Azure, GCP for specific workloads |

---

## Quick Start

### Compare Two Technologies

```
Compare React vs Vue for a SaaS dashboard.
Priorities: developer productivity (40%), ecosystem (30%), performance (30%).
```

### Calculate TCO

```
Calculate 5-year TCO for Next.js on Vercel.
Team: 8 developers. Hosting: $2500/month. Growth: 40%/year.
```

### Assess Migration

```
Evaluate migrating from Angular.js to React.
Codebase: 50,000 lines, 200 components. Team: 6 developers.
```

---

## Input Formats

The evaluator accepts three input formats:

**Text** - Natural language queries
```
Compare PostgreSQL vs MongoDB for our e-commerce platform.
```

**YAML** - Structured input for automation
```yaml
comparison:
  technologies: ["React", "Vue"]
  use_case: "SaaS dashboard"
  weights:
    ecosystem: 30
    performance: 25
    developer_experience: 45
```

**JSON** - Programmatic integration
```json
{
  "technologies": ["React", "Vue"],
  "use_case": "SaaS dashboard"
}
```

---

## Analysis Types

### Quick Comparison (200-300 tokens)
- Weighted scores and recommendation
- Top 3 decision factors
- Confidence level

### Standard Analysis (500-800 tokens)
- Comparison matrix
- TCO overview
- Security summary

### Full Report (1200-1500 tokens)
- All metrics and calculations
- Migration analysis
- Detailed recommendations

---

## Scripts

### `evaluate.py` — Unified CLI (recommended entry point)

```bash
# Compare two or more technologies
python scripts/evaluate.py compare --techs react vue --use-case "SaaS dashboard"

# Compare with custom weights (must be category=value pairs summing to 100)
python scripts/evaluate.py compare --techs postgres mongodb \
  --weights "performance=40,scalability=35,developer_experience=25"

# 5-year TCO analysis
python scripts/evaluate.py tco --technology "Next.js on Vercel" \
  --team 8 --monthly-hosting 2500 --growth 40

# Migration complexity estimate
python scripts/evaluate.py migrate --from "Angular.js" --to "React" \
  --loc 50000 --team 6

# JSON output for reports
python scripts/evaluate.py compare --techs react vue --output json
```

**Built-in profiles:** react, vue, angular, nextjs, postgres, mongodb.
For other technologies, pass `--config` with custom JSON data.

**Weighted criteria (adjustable):** performance, scalability, developer_experience, ecosystem, learning_curve, documentation, community_support, enterprise_readiness.

### Library scripts (for programmatic use)

The following scripts are importable Python libraries used by `evaluate.py`:

| Script | Class | Purpose |
|--------|-------|---------|
| `stack_comparator.py` | `StackComparator` | Weighted scoring across 8 criteria |
| `tco_calculator.py` | `TCOCalculator` | Multi-year cost projection |
| `migration_analyzer.py` | `MigrationAnalyzer` | Effort + risk estimation |
| `ecosystem_analyzer.py` | `EcosystemAnalyzer` | GitHub/npm health metrics |
| `security_assessor.py` | `SecurityAssessor` | CVE and compliance scoring |

---

## References

| Document | Content |
|----------|---------|
| `references/metrics.md` | Detailed scoring algorithms and calculation formulas |
| `references/examples.md` | Input/output examples for all analysis types |
| `references/workflows.md` | Step-by-step evaluation workflows |

---

## Confidence Levels

| Level | Score | Interpretation |
|-------|-------|----------------|
| High | 80-100% | Clear winner, strong data |
| Medium | 50-79% | Trade-offs present, moderate uncertainty |
| Low | < 50% | Close call, limited data |

---

## When to Use

- Comparing frontend/backend frameworks for new projects
- Evaluating cloud providers for specific workloads
- Planning technology migrations with risk assessment
- Calculating build vs. buy decisions with TCO
- Assessing open-source library viability

## When NOT to Use

- Trivial decisions between similar tools (use team preference)
- Mandated technology choices (decision already made)
- Emergency production issues (use monitoring tools)
