# AI Security Architecture Inference & Regression Detection

## Research question

> Can an AI agent infer an application's authorization model from contextual and runtime evidence and detect semantic authorization regressions across versions?

An AI-agent methodology and machine-readable schema for reconstructing a web
application's **security architecture** through authorized black-box
interaction — before generating or validating any security hypothesis.

This is a **methodology project**, not a scanner. The core idea: an AI agent
(or a human analyst) should first model actors, resources, relationships,
authorization rules, trust boundaries, and security invariants from
observable evidence, and only afterward generate cautious, evidence-scoped
hypotheses and validate them with minimal, reversible, explicitly authorized
tests.

The structured model is designed to act as a versioned security baseline, enabling authorization rules and invariants to be compared across application versions and semantic regressions to be identified.

## Why

Many "AI pentesting" approaches focus quickly on vulnerability discovery and exploitation. This project
argues for the opposite order:

```
OBSERVATION -> INFERENCE -> SECURITY INVARIANT -> SECURITY HYPOTHESIS -> VALIDATED FINDING
```

Every claim in the resulting model carries a status (`OBSERVED` / `INFERRED`
/ `CONFIRMED` / `PARTIALLY_CONFIRMED` / `REJECTED` / `UNRESOLVED`), a
confidence score, and a pointer to the exact evidence that produced it.
Nothing is asserted as fact without evidence, and no unvalidated hypothesis
is ever reported as a vulnerability.

## What's in this repo

- [`agent/`](agent/): the Security Architect agent itself: system prompt and the `security-architecture-analysis` skill (the single source of truth for the methodology).
- [`src/validate_model.py`](src/validate_model.py): deterministic validator for `security_model.json`.
- [`src/baseline.py`](src/baseline.py): validates and freezes a model as a comparison baseline.
- [`src/semantic_diff.py`](src/semantic_diff.py): compares authorization-rule semantics across two validated models and flags authorization weakenings as regression candidates.
- [`tests/test_semantic_diff.py`](tests/test_semantic_diff.py): unit tests for effect changes, evidence-only changes, condition ordering and rewording, rule additions/removals, and duplicate rule identities.
- [`examples/regression_demo/`](examples/regression_demo/): synthetic baseline → injected regression → expected semantic diff demonstration.
- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md): pointer to the skill file, kept for existing links.
- [`schema/security_model.schema.json`](schema/security_model.schema.json)
  — a JSON Schema for the structured `security_model.json` output format:
  actors, tenants, resources, relationships, atomic authorization rules,
  state machines, security invariants, hypotheses, coverage review, and
  validation results.
- [`examples/security_model.example.json`](examples/security_model.example.json)
  — a fully worked, **anonymized** example `security_model.json` for a
  fictional two-tenant SaaS app, illustrating ownership-based authorization,
  tenant isolation, and role-gated admin routes.
- [`examples/example-engagement-report.md`](examples/example-engagement-report.md)
  — a narrative write-up to accompany the example model, showing how
  evidence, hypotheses, and validation results are reported in prose.

## Validating a model

```bash
pip install -r requirements.txt
python src/validate_model.py examples/security_model.example.json
# VALID: examples/security_model.example.json (schema_version 1.1.0, 12 authorization rules)
```

`src/validate_model.py` runs JSON Schema validation plus the structural checks
used in the reference engagement: required top-level keys, atomic actions, no
combined actors, valid status/effect values, and `effect: "unknown"` for every
`UNRESOLVED` authorization rule. It exits non-zero on any issue.

## Comparing versions

Create a validated baseline snapshot:

```bash
python src/baseline.py examples/regression_demo/baseline.json \
  --output /tmp/baseline.json
```

Compare a later model against it:

```bash
python src/semantic_diff.py \
  examples/regression_demo/baseline.json \
  examples/regression_demo/changed.json \
  --output /tmp/diff.json
```

The current MVP matches authorization rules by canonical
`Actor × Resource × Action × Condition` identity. Condition order, whitespace,
confidence, status, evidence, and JSON ordering do not create a semantic
change. A `deny → allow` transition is classified as
`AUTHORIZATION_WEAKENING` and marked as a regression candidate; matching
baseline invariants are attached to the result. This first implementation is
intentionally deterministic: paraphrased or structurally changed conditions
are reported as rule removal/addition rather than matched with an LLM.

Run the unit tests with:

```bash
python -m unittest discover -s tests
```

## Status vocabulary

| Status | Meaning |
|---|---|
| `OBSERVED` | Directly seen (a response, a rendered page, a screenshot). |
| `INFERRED` | Reasoned from observations, not directly witnessed. |
| `CONFIRMED` | A specific, exact edge was actively validated and holds. |
| `PARTIALLY_CONFIRMED` | Some but not all important edges of a broader rule were validated; untested edges stay `INFERRED`/`UNRESOLVED`. |
| `REJECTED` | A hypothesis was actively tested and was not supported by the observed result. |
| `UNRESOLVED` | Genuinely unknown; not yet observed, inferred, or testable. |

## Atomic authorization modeling

Authorization is modeled at the granularity of:

```
Actor x Resource x Action x Condition -> allow / deny / unknown
```

Two actions on the same resource (e.g. Read vs. Delete) are never assumed to
share an authorization outcome unless the evidence shows they share the same
check. `effect: "unknown"` is used whenever a rule's `status` is
`UNRESOLVED` and the real allow/deny outcome hasn't actually been
established — an untested rule is never defaulted to `deny` just because
that reads as the "safer" guess.

## License

MIT — see [LICENSE](LICENSE).

## Disclaimer

This methodology is for **authorized** testing only. Nothing here condones
testing an application you do not own or do not have explicit permission to
test. Active validation (Phase 6) always requires explicit, scoped
authorization from the application owner before any state-changing test.
