#!/usr/bin/env python3
"""Validate a security_model.json against the Security Architect schema.

Formalizes only the checks used during the reference engagement:
  1. JSON Schema validation (schema/security_model.schema.json), using the
     validator for the schema's declared $schema, after checking the schema itself
  2. Required top-level structure
  3. Atomic authorization rules (one action per rule)
  4. No combined actors in authorization rules
  5. Valid status / effect values
  6. UNRESOLVED authorization rules must use effect "unknown"

Usage:
  python src/validate_model.py <model.json> [--schema <schema.json>]

Exit code 0 if valid, 1 if any check fails, 2 on usage/IO errors.
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover
    sys.exit("jsonschema is required: pip install -r requirements.txt")

DEFAULT_SCHEMA = Path(__file__).resolve().parent.parent / "schema" / "security_model.schema.json"

REQUIRED_TOP_LEVEL = [
    "schema_version", "app", "analysis_coverage", "actors", "tenants",
    "resources", "relationships", "authorization_rules", "state_machines",
    "security_invariants", "security_hypotheses", "coverage_review",
    "validation_results", "unresolved_questions",
]
STATUSES = {"OBSERVED", "INFERRED", "CONFIRMED", "PARTIALLY_CONFIRMED", "REJECTED", "UNRESOLVED"}
EFFECTS = {"allow", "deny", "unknown"}
ACTION_SEPARATORS = ("/", ",")
COMBINED_ACTOR_MARKERS = ("_or_",)
COMBINED_ACTOR_IDS = {"any_role"}


def check_schema(model, schema):
    validator_cls = jsonschema.validators.validator_for(schema)
    try:
        validator_cls.check_schema(schema)
    except jsonschema.exceptions.SchemaError as exc:
        return [f"schema: the schema itself is invalid: {exc.message}"]
    validator = validator_cls(schema)
    return [
        f"schema: {'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(model), key=lambda e: list(e.absolute_path))
    ]


def check_top_level(model):
    return [f"structure: missing top-level key '{k}'" for k in REQUIRED_TOP_LEVEL if k not in model]


def check_rules(model):
    errors = []
    for i, rule in enumerate(model.get("authorization_rules", [])):
        rid = rule.get("id", f"#{i}")
        action = rule.get("action")
        actor = rule.get("actor")
        status = rule.get("status")
        effect = rule.get("effect")

        if not isinstance(action, str) or any(s in action for s in ACTION_SEPARATORS):
            errors.append(f"atomicity: rule '{rid}' has a non-atomic action {action!r}")
        if not isinstance(actor, str) or actor in COMBINED_ACTOR_IDS or any(m in actor for m in COMBINED_ACTOR_MARKERS):
            errors.append(f"atomicity: rule '{rid}' has a combined actor {actor!r}")
        if status not in STATUSES:
            errors.append(f"values: rule '{rid}' has invalid status {status!r}")
        if effect not in EFFECTS:
            errors.append(f"values: rule '{rid}' has invalid effect {effect!r}")
        if status == "UNRESOLVED" and effect != "unknown":
            errors.append(f"consistency: rule '{rid}' is UNRESOLVED but effect is {effect!r} (must be 'unknown')")
    return errors


def validate(model, schema):
    return check_top_level(model) + check_schema(model, schema) + check_rules(model)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("model", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)

    try:
        model = json.loads(args.model.read_text())
        schema = json.loads(args.schema.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    errors = validate(model, schema)
    if errors:
        print(f"INVALID: {args.model} ({len(errors)} issue(s))")
        for e in errors:
            print(f"  - {e}")
        return 1
    rules = len(model.get("authorization_rules", []))
    print(f"VALID: {args.model} (schema_version {model.get('schema_version')}, {rules} authorization rules)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
