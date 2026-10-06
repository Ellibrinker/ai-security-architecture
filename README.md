# AI Security Architecture

## Research question

> Can an AI agent infer an application's authorization model from contextual and runtime evidence and detect semantic authorization regressions across versions?

An AI-agent methodology and machine-readable schema for reconstructing a web
application's **security architecture** from black-box, authorized
interaction — before generating or validating any security hypothesis.

This is a **methodology project**, not a scanner. The core idea: an AI agent
(or a human analyst) should first model actors, resources, relationships,
authorization rules, trust boundaries, and security invariants from
observable evidence, and only afterward generate cautious, evidence-scoped
hypotheses and validate them with minimal, reversible, explicitly authorized
tests.

## Why

Most "AI pentesting" demos jump straight to exploitation. This project
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

- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) — the full engagement
  methodology: the adaptive engagement flow, the atomic
  Actor × Resource × Action × Condition authorization model, the
  `DECLARED_ONLY` vs. `OBSERVED_IN_USE` execution-path distinction, resource
  lifecycle/state-machine modeling, and the seven-phase process
  (Exploration → Architecture Reconstruction → Invariants → Hypotheses →
  Coverage Review → Validation → Final Output).
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

## Status vocabulary

| Status | Meaning |
|---|---|
| `OBSERVED` | Directly seen (a response, a rendered page, a screenshot). |
| `INFERRED` | Reasoned from observations, not directly witnessed. |
| `CONFIRMED` | A specific, exact edge was actively validated and holds. |
| `PARTIALLY_CONFIRMED` | Some but not all important edges of a broader rule were validated; untested edges stay `INFERRED`/`UNRESOLVED`. |
| `REJECTED` | A hypothesis was actively tested and the suspected gap did not exist. |
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
