# Experiment Design

## Objective

This project evaluates two separate capabilities:

1. **Authorization-model inference** — whether the Security Architect can reconstruct an application's implemented authorization model from code/context and authorized runtime evidence.
2. **Semantic regression detection** — whether the system can detect meaningful authorization changes introduced between application versions.

The experiment is designed to separate the model being evaluated from the answer key used to score it.

---

## Core experimental flow

```text
Ground Truth v1
      ↓
Blind Security Architect run on v1
      ↓
Compare inferred model to Ground Truth
      ↓
Inject a controlled authorization regression
      ↓
Blind Security Architect run on v2
      ↓
Semantic diff: v1 baseline vs v2 model
      ↓
Measure inference and regression-detection performance
```

---

## 1. Freeze an application version

Each experiment starts from an application version that is treated as **v1**.

The experiment records enough version information to make the run reproducible, such as:

- application identifier
- deployment/version identifier when available
- source/schema fingerprints
- capture time
- relevant test fixtures

The application should remain unchanged while the v1 Ground Truth and blind evaluation are produced.

---

## 2. Build an independent Ground Truth

A separate Ground Truth Builder reconstructs the application's **implemented** authorization behavior from higher-confidence evidence such as:

- backend authorization logic
- entity RLS/FLS or equivalent policy configuration
- shared authorization helpers
- authenticated runtime checks when needed to resolve ambiguity

The Ground Truth Builder must not inspect the Security Architect's output before the Ground Truth is frozen.

Authorization is represented as atomic rules:

```text
Actor × Resource × Action × Condition → allow / deny / unknown
```

The Ground Truth also records security invariants, pre-existing weaknesses, and unresolved platform/runtime ambiguities.

### Ground Truth artifacts

A typical experiment produces:

- `ground_truth_v1.json` — scored atomic authorization rules
- `ground_truth_invariants_v1.json` — known security invariants
- `known_gaps_v1.json` — weaknesses already present in v1
- `experiment_scope_v1.md` — scored scope, exclusions, ambiguities, and regression candidate

### Important separation rules

- Pre-existing weaknesses are not treated as injected regressions.
- Unknown behavior is not converted to `deny` or `allow` without evidence.
- Platform semantics that cannot be verified are excluded from scoring or explicitly marked unknown.
- Client-side UI gating is not treated as server-side authorization proof.

---

## 3. Run the Security Architect blind on v1

After the Ground Truth is frozen, the Security Architect analyzes the same v1 application without access to the Ground Truth.

Its output is a structured `security_model.json` containing actors, resources, relationships, authorization rules, state transitions, invariants, evidence, confidence, and unresolved questions.

This produces the model that will be evaluated.

---

## 4. Evaluate authorization-model inference

The inferred model is compared against the frozen Ground Truth.

The evaluation should distinguish:

- correctly inferred authorization rules
- missed rules
- unsupported or invented rules
- correctly inferred security invariants
- unresolved cases handled as unknown rather than guessed
- false-positive security findings

Where the benchmark is large enough, report:

- precision
- recall
- F1
- false-positive rate

Evaluation is performed only over the pre-declared scored scope.

---

## 5. Inject one controlled regression

A **v2** version is created by deliberately changing one known authorization boundary.

A good injected regression should be:

- small and reversible
- localized to one enforcement point
- supported by a clear v1 Ground Truth rule
- outside the set of pre-existing known gaps
- unambiguous enough to test
- likely to preserve the same semantic rule identity between v1 and v2

Example:

```text
v1: org_admin(A) × Member(B) × SetStatus × cross-tenant → deny
v2: org_admin(A) × Member(B) × SetStatus × cross-tenant → allow
```

All unrelated behavior should remain unchanged as far as practical.

---

## 6. Run the Security Architect blind on v2

The Security Architect analyzes the modified version independently.

This produces a second structured authorization model.

The v1 and v2 models are then compared using the deterministic semantic-diff pipeline.

The current MVP matches rules by canonical:

```text
Actor × Resource × Action × Condition
```

and classifies effect changes such as `deny → allow` as authorization weakenings / regression candidates.

---

## 7. Evaluate regression detection

The regression evaluation asks:

- Was the injected authorization change represented in the v2 inferred model?
- Did the semantic diff identify the changed rule?
- Was the change classified as an authorization weakening when appropriate?
- Were unrelated rules incorrectly flagged as changed?
- Were relevant baseline invariants surfaced without overclaiming that they were definitively violated?

For multiple injected regressions, the benchmark can report:

- regression-detection precision
- regression-detection recall
- regression-detection F1
- false-positive rate
- per-regression error analysis

---

## 8. Expand from one experiment to a benchmark

A single v1 → v2 experiment is a proof of the evaluation protocol, not a full benchmark.

The benchmark should expand across multiple applications or scenarios with different authorization structures, for example:

- tenant isolation
- ownership checks
- privilege escalation
- role-gated actions
- workflow-role enforcement
- segregation of duties
- state-transition restrictions

Each scenario should include:

1. a known Ground Truth
2. a blind v1 inference run
3. one or more controlled regressions
4. a blind v2 inference run
5. semantic comparison
6. scored results and error analysis

The goal is to evaluate both **model reconstruction quality** and **regression-detection quality**, rather than relying on anecdotal demonstrations.

---

## Optional ablation

A useful extension is to compare:

- **context/code only**
- **context/code + runtime evidence**

This can measure whether runtime interaction materially improves authorization-rule and invariant inference.

---

## Threats to validity

Important limitations to document for each experiment include:

- incomplete runtime access
- platform behavior that cannot be independently verified
- missing test identities or fixtures
- ambiguous or conflicting enforcement layers
- non-deterministic application behavior
- differences between editor/sandbox source and deployed source
- semantic rule rewording that the deterministic diff currently treats as removal + addition

These limitations should be recorded rather than silently resolved through assumptions.

---

## Experimental principle

The experiment is intentionally structured so that:

> **the system is scored against a frozen answer key it did not see, on a versioned application whose authorization behavior is known before the regression is introduced.**

That separation is what turns the project from a security demo into an evaluation framework.
