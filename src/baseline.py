#!/usr/bin/env python3
"""Create a validated baseline snapshot from a security model.

Usage:
  python src/baseline.py <security_model.json> --output <baseline.json>
"""

import argparse
import json
import sys
from pathlib import Path

from validate_model import DEFAULT_SCHEMA, validate


def load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("model", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)

    try:
        model = load_json(args.model)
        schema = load_json(args.schema)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    errors = validate(model, schema)
    if errors:
        print(f"INVALID: {args.model} ({len(errors)} issue(s))", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"BASELINE: {args.output} "
        f"(schema_version {model.get('schema_version')}, "
        f"{len(model.get('authorization_rules', []))} authorization rules)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
