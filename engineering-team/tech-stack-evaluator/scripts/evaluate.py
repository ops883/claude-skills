#!/usr/bin/env python3
"""
evaluate.py — Unified CLI for the Technology Stack Evaluator.

Wraps the library scripts (stack_comparator, tco_calculator, ecosystem_analyzer,
security_assessor, migration_analyzer) behind a single CLI.

Usage:
    # Compare two technologies
    python scripts/evaluate.py compare --techs react vue --use-case "SaaS dashboard"

    # Compare with custom weights (must sum to 100)
    python scripts/evaluate.py compare --techs react vue --weights "developer_experience=40,ecosystem=35,performance=25"

    # TCO analysis
    python scripts/evaluate.py tco --technology "Next.js on Vercel" --team 8 --monthly-hosting 2500 --years 5

    # Migration estimate
    python scripts/evaluate.py migrate --from "Angular.js" --to "React" --loc 50000 --team 6

    # Load full config from JSON
    python scripts/evaluate.py --config config.json

    # JSON output
    python scripts/evaluate.py compare --techs postgres mongodb --output json
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Add scripts/ directory to path so we can import the library modules
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS_DIR)

try:
    from stack_comparator import StackComparator
    from tco_calculator import TCOCalculator
    from migration_analyzer import MigrationAnalyzer
    _HAS_LIBS = True
except ImportError:
    _HAS_LIBS = False


# ---------------------------------------------------------------------------
# Built-in knowledge base for common technologies
# (Used when no custom JSON config is provided)
# ---------------------------------------------------------------------------

TECH_PROFILES = {
    "react": {
        "performance": {"score": 82, "notes": "Virtual DOM, concurrent mode"},
        "scalability": {"score": 88, "notes": "Component model scales well"},
        "developer_experience": {"score": 85, "notes": "Rich ecosystem, great tooling"},
        "ecosystem": {"score": 95, "notes": "Largest frontend ecosystem"},
        "learning_curve": {"score": 65, "notes": "JSX, hooks, state management choices"},
        "documentation": {"score": 85, "notes": "Official docs are good"},
        "community_support": {"score": 95, "notes": "Massive community"},
        "enterprise_readiness": {"score": 90, "notes": "Used by Meta, Netflix, Airbnb"},
    },
    "vue": {
        "performance": {"score": 83, "notes": "Comparable to React"},
        "scalability": {"score": 80, "notes": "Good for small-medium scale"},
        "developer_experience": {"score": 90, "notes": "Gentle learning curve, Options/Composition API"},
        "ecosystem": {"score": 72, "notes": "Smaller than React but growing"},
        "learning_curve": {"score": 85, "notes": "Easiest major frontend framework"},
        "documentation": {"score": 92, "notes": "Best-in-class documentation"},
        "community_support": {"score": 78, "notes": "Strong but smaller than React"},
        "enterprise_readiness": {"score": 72, "notes": "Popular in Asia, Alibaba"},
    },
    "angular": {
        "performance": {"score": 78, "notes": "Zone.js overhead, improving with signals"},
        "scalability": {"score": 90, "notes": "Designed for large teams"},
        "developer_experience": {"score": 72, "notes": "Opinionated, steep initial curve"},
        "ecosystem": {"score": 78, "notes": "Mature, batteries-included"},
        "learning_curve": {"score": 45, "notes": "TypeScript, decorators, DI, RxJS"},
        "documentation": {"score": 80, "notes": "Good official docs"},
        "community_support": {"score": 75, "notes": "Strong enterprise community"},
        "enterprise_readiness": {"score": 95, "notes": "Designed for enterprise"},
    },
    "nextjs": {
        "performance": {"score": 90, "notes": "SSR, SSG, ISR, edge runtime"},
        "scalability": {"score": 88, "notes": "Vercel infrastructure"},
        "developer_experience": {"score": 88, "notes": "Zero-config, file-based routing"},
        "ecosystem": {"score": 90, "notes": "React ecosystem + Next.js community"},
        "learning_curve": {"score": 72, "notes": "Requires React knowledge first"},
        "documentation": {"score": 90, "notes": "Excellent docs and examples"},
        "community_support": {"score": 88, "notes": "Vercel-backed, large community"},
        "enterprise_readiness": {"score": 88, "notes": "Vercel, GitHub use it"},
    },
    "postgres": {
        "performance": {"score": 88, "notes": "Excellent for complex queries"},
        "scalability": {"score": 82, "notes": "Vertical + read replicas; horizontal is complex"},
        "developer_experience": {"score": 85, "notes": "SQL standard, pgAdmin, psql"},
        "ecosystem": {"score": 90, "notes": "Rich extension ecosystem"},
        "learning_curve": {"score": 80, "notes": "Standard SQL, good docs"},
        "documentation": {"score": 88, "notes": "Comprehensive official docs"},
        "community_support": {"score": 90, "notes": "25+ year track record"},
        "enterprise_readiness": {"score": 95, "notes": "Used everywhere"},
    },
    "mongodb": {
        "performance": {"score": 85, "notes": "Fast reads, good horizontal scale"},
        "scalability": {"score": 90, "notes": "Native horizontal sharding"},
        "developer_experience": {"score": 80, "notes": "JSON-like, flexible schema"},
        "ecosystem": {"score": 82, "notes": "Good ecosystem, Atlas cloud"},
        "learning_curve": {"score": 82, "notes": "Easy for JavaScript developers"},
        "documentation": {"score": 82, "notes": "Good official docs"},
        "community_support": {"score": 80, "notes": "Large community"},
        "enterprise_readiness": {"score": 80, "notes": "Atlas managed service"},
    },
}


def normalize_tech_name(name: str) -> str:
    return name.lower().replace(" ", "").replace(".", "").replace("-", "").replace("_", "")


def lookup_tech(name: str) -> Optional[Dict]:
    key = normalize_tech_name(name)
    for profile_name, data in TECH_PROFILES.items():
        if normalize_tech_name(profile_name) == key:
            return data
    return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_compare(args, output_format: str) -> int:
    if len(args.techs) < 2:
        print("Error: --techs requires at least 2 technology names", file=sys.stderr)
        return 2

    # Build weights
    weights = {}
    if args.weights:
        for part in args.weights.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                try:
                    weights[k.strip()] = float(v.strip())
                except ValueError:
                    pass

    # Build comparison data
    technologies = []
    missing = []
    for name in args.techs:
        profile = lookup_tech(name)
        if profile:
            technologies.append({"name": name, **profile})
        else:
            missing.append(name)

    if missing:
        print(f"Warning: no built-in profile for: {', '.join(missing)}", file=sys.stderr)
        print("  Use --config to provide custom data, or scores default to 50.", file=sys.stderr)
        for name in missing:
            technologies.append({"name": name})

    if not _HAS_LIBS:
        print("Error: could not import StackComparator from stack_comparator.py", file=sys.stderr)
        return 1

    comparison_data = {
        "technologies": technologies,
        "use_case": args.use_case or "general",
        "weights": weights,
    }
    comparator = StackComparator(comparison_data)

    # Score each tech
    results = {}
    for tech in technologies:
        name = tech["name"]
        scores = comparator.score_technology(name, tech)
        weighted_total = sum(
            scores.get(cat, 50.0) * (comparator.weights.get(cat, 0) / 100)
            for cat in comparator.FEATURE_CATEGORIES
        )
        results[name] = {"scores": scores, "total": weighted_total}

    # Sort by total
    ranked = sorted(results.items(), key=lambda x: x[1]["total"], reverse=True)

    if output_format == "json":
        print(json.dumps({
            "use_case": comparison_data["use_case"],
            "weights": comparator.weights,
            "results": [
                {"technology": name, "total_score": round(data["total"], 1), "scores": {k: round(v, 1) for k, v in data["scores"].items()}}
                for name, data in ranked
            ],
            "recommendation": ranked[0][0] if ranked else None,
        }, indent=2))
    else:
        use_case_label = f" for {args.use_case}" if args.use_case else ""
        print(f"\nTechnology Comparison{use_case_label}")
        print("=" * 55)
        print(f"{'Technology':<20} {'Score':>7}  {'Rank':<6}")
        print("-" * 35)
        for i, (name, data) in enumerate(ranked, 1):
            rank_label = "★ Recommended" if i == 1 else f"#{i}"
            print(f"  {name:<18} {data['total']:>6.1f}  {rank_label}")

        print(f"\nWeighted criteria ({args.use_case or 'default'}):")
        for cat, weight in sorted(comparator.weights.items(), key=lambda x: -x[1]):
            if weight > 0:
                print(f"  {cat:<30} {weight:.0f}%")

        print(f"\nRecommendation: {ranked[0][0]}" if ranked else "")

    return 0


def cmd_tco(args, output_format: str) -> int:
    if not _HAS_LIBS:
        print("Error: could not import TCOCalculator", file=sys.stderr)
        return 1

    tco_data = {
        "technology": args.technology,
        "team_size": args.team or 5,
        "timeline_years": args.years or 5,
        "initial_costs": {
            "training": (args.team or 5) * 2000,
            "setup": 5000,
        },
        "operational_costs": {
            "monthly_hosting": args.monthly_hosting or 500,
            "annual_support": 0,
        },
        "scaling_params": {"annual_growth_rate": (args.growth or 20) / 100},
        "productivity_factors": {"onboarding_weeks": 4},
    }
    calculator = TCOCalculator(tco_data)
    initial = calculator.calculate_initial_costs()
    operational = calculator.calculate_operational_costs()

    total_5yr = initial.get("total_initial", 0) + sum(operational.get("total_yearly", []))

    if output_format == "json":
        print(json.dumps({
            "technology": args.technology,
            "team_size": tco_data["team_size"],
            "years": tco_data["timeline_years"],
            "initial_costs": {k: round(v, 0) for k, v in initial.items()},
            "total_5yr": round(total_5yr, 0),
        }, indent=2))
    else:
        print(f"\nTCO Analysis: {args.technology}")
        print("=" * 55)
        print(f"Team size: {tco_data['team_size']} developers")
        print(f"Timeline:  {tco_data['timeline_years']} years")
        print(f"Hosting:   ${args.monthly_hosting or 500:,}/month")
        print(f"Growth:    {args.growth or 20}%/year\n")
        print(f"Initial costs:")
        for k, v in initial.items():
            if k != "total_initial" and v > 0:
                print(f"  {k:<25} ${v:>10,.0f}")
        print(f"  {'Total initial':<25} ${initial.get('total_initial', 0):>10,.0f}")
        print(f"\nTotal {tco_data['timeline_years']}-year cost:     ${total_5yr:>10,.0f}")

    return 0


def cmd_migrate(args, output_format: str) -> int:
    if not _HAS_LIBS:
        print("Error: could not import MigrationAnalyzer", file=sys.stderr)
        return 1

    migration_data = {
        "from_technology": args.from_tech,
        "to_technology": args.to_tech,
        "codebase_size": args.loc or 10000,
        "team_size": args.team or 5,
        "timeline_months": args.months or 12,
    }
    analyzer = MigrationAnalyzer(migration_data)
    try:
        analysis = analyzer.analyze_migration()
    except Exception as e:
        print(f"Analysis error: {e}", file=sys.stderr)
        analysis = {"complexity": "Unknown", "effort_developer_months": "N/A"}

    if output_format == "json":
        print(json.dumps({"from": args.from_tech, "to": args.to_tech, **analysis}, indent=2))
    else:
        print(f"\nMigration Analysis: {args.from_tech} → {args.to_tech}")
        print("=" * 55)
        print(f"Codebase: {(args.loc or 10000):,} lines, {args.team or 5} developers")
        for k, v in analysis.items():
            label = k.replace("_", " ").capitalize()
            print(f"  {label:<35} {v}")

    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Technology Stack Evaluator — compare, TCO, migration analysis"
    )
    parser.add_argument("--config", help="JSON config file")
    parser.add_argument("--output", choices=["text", "json"], default="text")

    sub = parser.add_subparsers(dest="command")

    # compare
    cp = sub.add_parser("compare", help="Compare technology stacks")
    cp.add_argument("--techs", nargs="+", required=True, help="Technologies to compare")
    cp.add_argument("--use-case", help="Use case context (e.g. 'SaaS dashboard')")
    cp.add_argument("--weights", help="Comma-separated weights: 'developer_experience=40,ecosystem=35'")

    # tco
    tco = sub.add_parser("tco", help="Total cost of ownership analysis")
    tco.add_argument("--technology", required=True, help="Technology name")
    tco.add_argument("--team", type=int, help="Team size (developers)")
    tco.add_argument("--monthly-hosting", type=float, help="Monthly hosting cost in USD")
    tco.add_argument("--years", type=int, default=5, help="Projection years (default: 5)")
    tco.add_argument("--growth", type=float, default=20, help="Annual growth rate % (default: 20)")

    # migrate
    mg = sub.add_parser("migrate", help="Migration complexity and effort estimate")
    mg.add_argument("--from", dest="from_tech", required=True, help="Source technology")
    mg.add_argument("--to", dest="to_tech", required=True, help="Target technology")
    mg.add_argument("--loc", type=int, help="Lines of code in codebase")
    mg.add_argument("--team", type=int, help="Team size")
    mg.add_argument("--months", type=int, help="Available timeline in months")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "compare":
        return cmd_compare(args, args.output)
    elif args.command == "tco":
        return cmd_tco(args, args.output)
    elif args.command == "migrate":
        return cmd_migrate(args, args.output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
