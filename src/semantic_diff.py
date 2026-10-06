#!/usr/bin/env python3
"""Compare two validated security models and report semantic authorization changes.

The comparison is structural rather than line-based. Authorization rules are
matched by canonical (actor, resource, action, conditions) identity; evidence,
confidence, status, and JSON ordering do not affect rule identity.

Usage:
  python src/semantic_diff.py <baseline.json> <current.json> [--output <diff.json>]
"""

import argparse
import json
import re
import sys
from pathlib import Path

from validate_model import DEFAULT_SCHEMA, validate


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc


def normalize_text(value):
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value.strip().lower())


def canonical_conditions(conditions):
    return tuple(sorted(normalize_text(c) for c in conditions if isinstance(c, str)))


def rule_key(rule):
    return (
        normalize_text(rule.get("actor")),
        normalize_text(rule.get("resource")),
        normalize_text(rule.get("action")),
        canonical_conditions(rule.get("conditions", [])),
    )


def build_rule_index(model):
    index = {}
    for rule in model.get("authorization_rules", []):
        key = rule_key(rule)
        if key in index:
            first = index[key].get("id", "<unknown>")
            second = rule.get("id", "<unknown>")
            raise ValueError(
                "duplicate semantic authorization rule identity: "
                f"{first!r} and {second!r}"
            )
        index[key] = rule
    return index


def matching_invariants(model, rule):
    actor = normalize_text(rule.get("actor"))
    resource = normalize_text(rule.get("resource"))
    action = normalize_text(rule.get("action"))
    matches = []

    for invariant in model.get("security_invariants", []):
        actors = {normalize_text(v) for v in invariant.get("affected_actors", [])}
        resources = {normalize_text(v) for v in invariant.get("affected_resources", [])}
        actions = {normalize_text(v) for v in invariant.get("affected_actions", [])}

        if actor in actors and resource in resources and action in actions:
            matches.append({
                "id": invariant.get("id"),
                "statement": invariant.get("statement"),
                "status": invariant.get("status"),
            })
    return matches


def classify_effect_change(before, after):
    if before == after:
        return None, False

    mapping = {
        ("deny", "allow"): ("AUTHORIZATION_WEAKENING", True),
        ("allow", "deny"): ("AUTHORIZATION_RESTRICTION", False),
        ("unknown", "allow"): ("NEWLY_OBSERVED_ALLOW", False),
        ("unknown", "deny"): ("NEWLY_OBSERVED_DENY", False),
        ("allow", "unknown"): ("AUTHORIZATION_BECAME_UNRESOLVED", False),
        ("deny", "unknown"): ("AUTHORIZATION_BECAME_UNRESOLVED", False),
    }
    return mapping[(before, after)]


def _change_from_rule(
    change_type,
    rule,
    *,
    regression_candidate,
    baseline_effect=None,
    current_effect=None,
):
    return {
        "type": change_type,
        "regression_candidate": regression_candidate,
        "actor": rule.get("actor"),
        "resource": rule.get("resource"),
        "action": rule.get("action"),
        "conditions": rule.get("conditions", []),
        "baseline_effect": baseline_effect,
        "current_effect": current_effect,
        "baseline_status": None,
        "current_status": None,
        "baseline_rule_id": None,
        "current_rule_id": None,
        "violated_invariants": [],
    }


def compare_models(baseline, current):
    baseline_index = build_rule_index(baseline)
    current_index = build_rule_index(current)
    changes = []

    for key in sorted(set(baseline_index) | set(current_index)):
        before = baseline_index.get(key)
        after = current_index.get(key)

        if before is None:
            change = _change_from_rule(
                "RULE_ADDED",
                after,
                regression_candidate=False,
                baseline_effect=None,
                current_effect=after.get("effect"),
            )
            change["current_status"] = after.get("status")
            change["current_rule_id"] = after.get("id")
            changes.append(change)
            continue

        if after is None:
            change = _change_from_rule(
                "RULE_REMOVED",
                before,
                regression_candidate=False,
                baseline_effect=before.get("effect"),
                current_effect=None,
            )
            change["baseline_status"] = before.get("status")
            change["baseline_rule_id"] = before.get("id")
            changes.append(change)
            continue

        change_type, regression_candidate = classify_effect_change(
            before.get("effect"), after.get("effect")
        )
        if change_type is None:
            continue

        change = _change_from_rule(
            change_type,
            after,
            regression_candidate=regression_candidate,
            baseline_effect=before.get("effect"),
            current_effect=after.get("effect"),
        )
        change["baseline_status"] = before.get("status")
        change["current_status"] = after.get("status")
        change["baseline_rule_id"] = before.get("id")
        change["current_rule_id"] = after.get("id")
        if regression_candidate:
            change["violated_invariants"] = matching_invariants(baseline, before)
        changes.append(change)

    return {
        "baseline_schema_version": baseline.get("schema_version"),
        "current_schema_version": current.get("schema_version"),
        "summary": {
            "total_changes": len(changes),
            "regression_candidates": sum(
                1 for c in changes if c["regression_candidate"]
            ),
            "authorization_weakenings": sum(
                1 for c in changes if c["type"] == "AUTHORIZATION_WEAKENING"
            ),
            "authorization_restrictions": sum(
                1 for c in changes if c["type"] == "AUTHORIZATION_RESTRICTION"
            ),
            "rules_added": sum(1 for c in changes if c["type"] == "RULE_ADDED"),
            "rules_removed": sum(
                1 for c in changes if c["type"] == "RULE_REMOVED"
            ),
        },
        "changes": changes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("baseline", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)

    try:
        baseline = load_json(args.baseline)
        current = load_json(args.current)
        schema = load_json(args.schema)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    invalid = False
    for label, path, model in (
        ("baseline", args.baseline, baseline),
        ("current", args.current, current),
    ):
        errors = validate(model, schema)
        if errors:
            invalid = True
            print(
                f"INVALID {label}: {path} ({len(errors)} issue(s))",
                file=sys.stderr,
            )
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
    if invalid:
        return 1

    try:
        result = compare_models(baseline, current)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered)
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(
            f"DIFF: {args.output} "
            f"({result['summary']['total_changes']} changes, "
            f"{result['summary']['regression_candidates']} regression candidate(s))"
        )
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
