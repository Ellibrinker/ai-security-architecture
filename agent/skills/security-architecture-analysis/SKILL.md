---
name: security-architecture-analysis
description: Rigorous black-box methodology for reconstructing a web application's security architecture (actors, resources, trust boundaries, invariants) before generating and validating security hypotheses. Reusable across any target web application.
argument-hint: [target-url]
---

# Security Architecture Analysis

## Purpose

This is a methodology skill, not a scanner. The goal is NOT to immediately hunt
for vulnerabilities. The agent must first reconstruct the application's
security architecture from observable, black-box evidence, then infer security
invariants, and only afterward generate and cautiously validate security
hypotheses.

This skill applies to any target web application. It contains no
platform-specific assumptions and must not assume access to source code,
internal platform metadata, database schemas, or implementation details unless
those are explicitly provided as part of the authorized test.

## Adaptive Engagement Flow (self-guided, minimal upfront input)

The minimum input to start is a **target URL**. Do not front-load a
questionnaire asking for authorization scope, test accounts, roles, tenants,
or constraints before beginning. Instead:

1. **Start immediately with safe, non-invasive exploration** (Phase 1) using
   only what an anonymous visitor can see: the target URL is enough
   authorization for read-only, black-box exploration of a target the user
   has identified as theirs (or theirs to test).
2. **Drive the seven phases autonomously.** Do not wait for the user to say
   "run Phase 1-3" or "continue to Phase 4". Progress phase by phase as long
   as the evidence and authorization already available support it. Update
   the Application Security Graph continuously as you go.
3. **Request additional input only when there is a concrete, current reason
   for it** - i.e. you have hit a specific point where more access or
   information would let you resolve a specific unresolved part of the
   architecture. Ask for exactly what that point requires, not everything
   that might eventually be useful. Examples:
   - Exploration reaches a login wall and anonymous access can't go
     further -> ask for one test account.
   - A second role (e.g. Admin) is visible or implied but not accessible ->
     ask whether an account with that role can be provided, naming the
     specific authorization boundary it would let you reconstruct.
   - A tenant/organization boundary is discovered and understanding
     isolation requires a second tenant -> ask for an account in another
     tenant, naming the isolation boundary in question.
   - A discovered workflow's intended behavior is ambiguous (e.g. is this
     transition supposed to be reachable by a non-owner?) -> ask one focused
     clarifying question instead of guessing or silently assuming.
   - You are about to move from modeling/hypotheses (Phases 1-5) into active
     testing (Phase 6) -> stop and ask for explicit authorization and scope
     (see below). This gate is never skipped or weakened by the adaptive flow.
4. **Keep asks small and justified.** Each request should be answerable in
   one reply and should state, briefly, what it unlocks (which role, tenant
   boundary, workflow, or unresolved architecture question it resolves).
   Batch a request only when multiple concrete needs have accumulated at the
   same pause point - do not pre-emptively collect credentials "just in
   case."
5. **Pause only when genuinely blocked**, i.e. when continuing would require
   guessing, inventing architecture, exceeding current access, or crossing
   into active validation without authorization. Otherwise, keep moving
   through the phases in the same turn/session.

**Explicit authorization before Phase 6 remains mandatory and is not weakened
by this adaptive flow.** No matter how much of Phases 1-5 was completed
autonomously, active validation requires the user to explicitly confirm scope
(what's in bounds, what's excluded, e.g. no destructive actions) before any
test that could change state or access another party's data. If that
authorization is missing or ambiguous when Phase 6 is reached, stop and ask -
do not infer consent from the fact that a target URL was provided.

Constraints (rate limits, no destructive actions, time windows, etc.) can
likewise be gathered adaptively: state the specific test you intend to run
and ask if it's acceptable, rather than requesting a general constraints list
upfront.

## Strict Lifecycle (never skip or reorder)

```
OBSERVATION -> INFERENCE -> SECURITY INVARIANT -> SECURITY HYPOTHESIS -> VALIDATED FINDING
```

Never present an inference as a confirmed fact. Never report an unvalidated
hypothesis as a vulnerability. Evidence before conclusions, always. When new
evidence contradicts an earlier inference (at any phase), revise the earlier
record rather than silently accumulating a contradiction - note what changed
and why.

## Status Vocabulary

Use consistently across the graph:

- `OBSERVED` - directly seen (a response, a rendered page, a screenshot).
- `INFERRED` - reasoned from observations, not directly witnessed.
- `CONFIRMED` - a specific, exact edge was actively validated and holds.
- `PARTIALLY_CONFIRMED` - some but not all important edges of a broader rule
  were validated; the untested edges stay INFERRED or UNRESOLVED. Never
  collapse this to `CONFIRMED` for the whole rule.
- `REJECTED` - a hypothesis was actively tested and was not supported by the
  observed result.
- `UNRESOLVED` - genuinely unknown; not yet observed, inferred, or testable
  within current scope.

## Execution-Path Evidence (declared vs. actually used)

Client bundles, SDKs, and platform documentation routinely expose endpoints,
methods, or capabilities that the application does not actually use. Treat
"appears in code/SDK" and "is part of the application's active architecture"
as two different claims with two different evidence classes:

- `DECLARED_ONLY` - the endpoint/method/capability exists in client code, an
  SDK, a manifest, or documentation, but no observed application behavior
  has exercised it.
- `OBSERVED_IN_USE` - the application was actually seen invoking this path
  (a real UI-driven request, a captured/replayed call that produced the
  behavior seen through the UI, or an explicit response tying the path to
  real data).

Never promote a `DECLARED_ONLY` path to being "the" mechanism behind an
observed behavior without evidence connecting the two. If a generic-looking
API (e.g. a platform's default CRUD layer) is present alongside a custom
endpoint, and both could plausibly explain observed behavior, test or state
explicitly which one is actually driving it before relying on either in later
reasoning. Record every discovered path with its execution-path status and
the evidence (or absence of evidence) for that status. Architecture
conclusions (trust boundaries, invariants) should be built on `OBSERVED_IN_USE`
paths; `DECLARED_ONLY` paths belong in the attack surface as unresolved/
lower-confidence candidates, not as confirmed architecture.

## Atomic Authorization Modeling

Model authorization at the granularity of:

```
Actor x Resource x Action x Condition -> allow / deny / unknown
```

- `Actor`: a role, a relationship to the resource (owner, member,
  non-member), or an authentication state.
- `Resource`: the specific entity/type, not a vague grouping.
- `Action`: exactly one of Create, Read, Update, Delete, List, Invite, Share,
  Approve, Administer, etc. Never bundle multiple actions (e.g. "edit/delete")
  into a single rule.
- `Condition`: ownership, tenant/org membership, resource state, or other
  qualifiers that change the outcome.

Each rule gets its own status, confidence, and evidence, independent of
sibling rules on the same resource. Two actions on the same resource (e.g.
Read vs. Delete) may have different authorization outcomes - do not assume
they share a rule unless evidence shows the same check governs both (e.g.
identical error message/behavior observed for both, or a stated/observed
shared code path). Even when evidence is shared across actions, emit one
separate rule per action and point each rule at the same shared evidence.

## Resource Lifecycle and State Machines

For every stateful resource or workflow discovered (e.g. draft -> published,
pending -> approved -> rejected, invitation pending -> accepted -> revoked),
reconstruct:

- The set of states.
- Permitted transitions between states.
- Who (which actor/role/relationship) may trigger each transition.
- Under what condition each transition is allowed (e.g. only from a specific
  prior state, only before a deadline, only by the resource owner).
- Transitions that were never observed or could not be determined -
  explicitly listed as unresolved, not silently omitted.

Treat lifecycle/state-transition boundaries as first-class parts of the
security architecture, on the same footing as RBAC, ownership, and tenant
boundaries - a missing transition guard (e.g. "revoked" never actually
blocking access) is as material a finding as a missing role check.

## Persistent Application Security Graph

Maintain a structured record (a JSON or Markdown file in the conversation
workspace, e.g. `security_graph_<target>.json`) with two logically separate
sections:

### A. Security Architecture Model (the reusable output of Phases 1-3)

Keep this as a distinct, self-contained artifact so later analysis stages (or
future engagements against the same target) can reuse it without re-deriving
it. It contains:

- Actors and roles
- Resources
- Relationships (ownership, membership, parent/child, tenant boundaries)
- Actions
- Authorization rules, modeled atomically as Actor x Resource x Action x
  Condition (see above)
- Ownership model
- Tenant boundaries
- Trust boundaries (anonymous->authenticated, frontend->backend,
  application->external service)
- State machines (per stateful resource/workflow)
- Observed execution paths (with DECLARED_ONLY / OBSERVED_IN_USE status)
- Security invariants
- Unresolved questions

### B. Hypotheses and Findings (produced in later phases)

Kept separate from section A so the architecture model isn't polluted by
speculative or in-progress hypothesis work:

- Security hypotheses
- Coverage review / coverage gaps
- Validated findings (CONFIRMED / PARTIALLY_CONFIRMED / REJECTED)

For every architectural assertion, record:
- `assertion`
- `status` (see Status Vocabulary)
- `confidence`: 0-100
- `supporting evidence`
- `evidence source` (exact page, request, response, or interaction)

Update this graph incrementally as each phase produces new evidence. Do not
overwrite prior evidence: append and refine, and explicitly note when new
evidence revises an earlier entry.

## Structured Security Model Output (security_model.json)

In addition to the narrative Markdown graph/report, produce and maintain a
machine-readable `security_model.json` for every analyzed application,
alongside the Markdown artifacts in the conversation workspace (e.g.
`security_model_<target>.json`). This is the structured, reusable counterpart
of Section A (the Security Architecture Model) plus the Section B
hypotheses/findings - application-agnostic, so it can later serve as a
comparison baseline for the same target (diffing is out of scope for now;
just make sure the file is complete and well-formed enough to serve as one).

Update it incrementally alongside the Markdown graph - do not treat it as a
final-step export. Every assertion inside it carries its own `status`
(Status Vocabulary), `confidence` (0-100), `evidence`, and `evidence_source`,
exactly as in the Markdown graph - this file is a structured mirror of that
evidence, not a separate, less-rigorous summary.

Required top-level shape:

```json
{
  "schema_version": "1.1.0",
  "app": {
    "target_url": "",
    "app_name": "",
    "analysis_date": "",
    "engagement_scope": "",
    "notes": ""
  },
  "analysis_coverage": {
    "actors": "NOT_ANALYZED|PARTIAL|COMPLETE",
    "tenants": "NOT_ANALYZED|PARTIAL|COMPLETE",
    "resources": "NOT_ANALYZED|PARTIAL|COMPLETE",
    "relationships": "NOT_ANALYZED|PARTIAL|COMPLETE",
    "authorization_rules": "NOT_ANALYZED|PARTIAL|COMPLETE",
    "state_machines": "NOT_ANALYZED|PARTIAL|COMPLETE",
    "security_invariants": "NOT_ANALYZED|PARTIAL|COMPLETE",
    "validation_results": "NOT_ANALYZED|PARTIAL|COMPLETE"
  },
  "actors": [
    {
      "id": "", "name": "", "description": "",
      "roles": [""],
      "status": "OBSERVED|INFERRED|CONFIRMED|PARTIALLY_CONFIRMED|REJECTED|UNRESOLVED",
      "confidence": 0, "evidence": "", "evidence_source": ""
    }
  ],
  "tenants": [
    {
      "id": "", "name": "", "description": "",
      "status": "...", "confidence": 0, "evidence": "", "evidence_source": ""
    }
  ],
  "resources": [
    {
      "id": "", "name": "", "description": "",
      "tenant_scoped": true,
      "status": "...", "confidence": 0, "evidence": "", "evidence_source": ""
    }
  ],
  "relationships": [
    {
      "id": "", "type": "ownership|membership|parent_child|tenant_boundary|other",
      "from": "", "to": "", "description": "",
      "status": "...", "confidence": 0, "evidence": "", "evidence_source": ""
    }
  ],
  "authorization_rules": [
    {
      "id": "",
      "actor": "",
      "resource": "",
      "action": "Create|Read|Update|Delete|List|Invite|Share|Approve|Administer|Other",
      "conditions": [""],
      "effect": "allow|deny|unknown",
      "execution_path_status": "DECLARED_ONLY|OBSERVED_IN_USE|not_applicable",
      "status": "...", "confidence": 0, "evidence": "", "evidence_source": ""
    }
  ],
  "state_machines": [
    {
      "id": "", "resource": "",
      "states": [""],
      "transitions": [
        {
          "from": "", "to": "",
          "allowed_actors": [""],
          "conditions": [""],
          "status": "...", "confidence": 0, "evidence": "", "evidence_source": ""
        }
      ],
      "unresolved_transitions": [""]
    }
  ],
  "security_invariants": [
    {
      "id": "", "statement": "",
      "affected_actors": [""], "affected_resources": [""], "affected_actions": [""],
      "status": "...", "confidence": 0, "evidence": "", "evidence_source": ""
    }
  ],
  "security_hypotheses": [
    {
      "id": "", "challenges_rule_id_or_invariant_id": "",
      "actor": "", "resource": "", "action": "", "condition": "",
      "suspected_execution_path": "", "execution_path_status": "DECLARED_ONLY|OBSERVED_IN_USE",
      "evidence": "", "missing_or_uncertain_control": "",
      "confidence": 0, "minimal_validation_method": ""
    }
  ],
  "coverage_review": {
    "dimensions_reviewed": ["actors", "resources", "actions", "conditions",
      "tenant_boundaries", "ownership_boundaries", "privileged_operations",
      "state_transitions"],
    "coverage_gaps": [
      { "id": "", "description": "", "dimension": "" }
    ]
  },
  "validation_results": [
    {
      "id": "", "hypothesis_id": "",
      "rule_ids_tested": [""],
      "actor": "", "resource": "", "action": "", "condition_tested": "",
      "test_performed": "", "evidence": "",
      "result_status": "CONFIRMED|PARTIALLY_CONFIRMED|REJECTED|UNRESOLVED",
      "unresolved_edges": [""],
      "notes": ""
    }
  ],
  "unresolved_questions": [
    { "id": "", "description": "", "related_to": [""], "why_unresolved": "" }
  ]
}
```

Rules specific to this file:

- **Atomicity is mandatory in `authorization_rules`**: one `action` value per
  rule entry. Never represent "read/update/delete" as a single rule with a
  combined action string - if Read, Update, and Delete share identical
  evidence and behavior, still emit three entries (one per action), each
  pointing at the same shared evidence, rather than collapsing them.
- `schema_version` follows semver (`MAJOR.MINOR.PATCH`). Bump it only when
  this skill's required shape actually changes, so models produced at
  different times stay comparable. Do not bump it per-engagement.
- `authorization_rules[].effect` is `allow`, `deny`, or `unknown`. Use `unknown`
  whenever the rule's `status` is `UNRESOLVED` and the actual authorization
  outcome (allow vs deny) has not actually been established - never default
  an untested rule to `deny` just because that is the safer-sounding guess.
- Arrays alone cannot distinguish "checked, found none" from "not analyzed"
  (an empty array looks the same either way). Use the top-level
  `analysis_coverage` object for that distinction instead: set each listed
  section's status to `NOT_ANALYZED` before that part of the methodology has
  been attempted, `PARTIAL` once some evidence exists but the section isn't
  believed complete (e.g. only one role or one tenant explored so far), and
  `COMPLETE` only when you assess that section as reasonably exhaustive given
  current access. Update these statuses as you go, phase by phase - do not
  leave them all `NOT_ANALYZED` until the end, and do not mark `COMPLETE`
  prematurely just because the array is non-empty.
- Every array may still be empty but should remain present with the key, so a
  reader can see what was modeled (even as "none found") alongside the
  matching `analysis_coverage` status.
- This file is the baseline artifact for any future comparison/diff work -
  do not build diffing now, just make sure the file is internally consistent
  and complete enough to be diffed later.

## Phase 1: Application Exploration

Begin here automatically once a target URL is available - no further input is
required to start. Explore the application as a normal (initially anonymous)
user using available browser capabilities (navigate, click, fill forms,
follow links). No active vulnerability testing in this phase.

Map:
- Pages and routes
- Authentication flows (signup, login, password reset, SSO, MFA)
- Visible roles (e.g. admin, member, viewer)
- Resources/entities visible through the UI
- User actions available at each screen
- Organization/team/workspace concepts, if any
- Ownership relationships (who "owns" what)
- Invitation and sharing flows
- Privileged functionality (admin panels, settings, billing, exports)
- Stateful resources/workflows and the transitions observed (e.g. draft ->
  published, pending -> approved)

Do not assume access to source code, internal platform internals, database
schemas, or metadata beyond what's observable through the app itself, unless
explicitly provided. If exploration hits a wall that only a test account can
pass (e.g. a login screen with no way to observe past it), pause and ask for
one test account, stating what it would let you explore next - then continue.

## Phase 2: Architecture Reconstruction

Proceed here automatically once Phase 1 evidence exists, without waiting for
a prompt. From Phase 1 evidence, populate the Security Architecture Model
(section A):
- Actors, Roles, Resources, Relationships, Actions
- Authorization rules at Actor x Resource x Action x Condition granularity
- Ownership model
- Tenant boundaries (org -> org, workspace -> workspace)
- Trust boundaries (frontend -> backend, application -> external service)
- State machines for every stateful resource/workflow identified, with
  transitions, permitted actors, and conditions
- Observed execution paths, each tagged DECLARED_ONLY or OBSERVED_IN_USE

Every assertion gets a status, confidence score, evidence, and evidence
source. Do not skip weakly-supported areas: record them as low-confidence
INFERRED with an accompanying "unresolved question" instead of omitting them.
Do not infer that an endpoint, SDK method, or client function is part of the
active architecture merely because it appears in a bundle or manifest - that
alone only supports DECLARED_ONLY. If reconstructing a boundary (a second
role, a second tenant) genuinely requires access you don't have, pause and
ask for it there, naming the boundary - then continue.

## Phase 3: Security Invariants

Continue automatically from Phase 2. Infer the rules that appear to define
the intended security model, e.g.:
- "A user may only access resources belonging to their organization."
- "Only organization administrators may manage members."
- "A revoked authorization artifact should no longer grant access."

Ground each invariant in the atomic authorization rules and/or state machines
from Phase 2 rather than stating it more broadly than the evidence supports.
If Read and Delete on the same resource have different evidence, express
that as two invariants (or one invariant with explicitly scoped sub-claims),
not one merged claim.

Each invariant records:
- ID
- Affected actor(s)
- Affected resource(s)
- Affected action(s) (explicit - do not default to "all actions")
- Expected rule
- Evidence
- Confidence

This completes the Security Architecture Model (section A). Treat it as a
stable artifact from here on: later phases may add hypotheses and findings
about it, but revise section A itself only when new evidence actually
contradicts it.

## Phase 4: Attack Surface Mapping

Continue automatically once the architecture model exists - only after it
exists, identify:
- User-controlled identifiers (IDs in URLs/params, slugs, tokens)
- Sensitive resources
- Privileged actions
- Tenant boundaries
- Role boundaries
- Authentication transitions
- Invitation/share flows
- State transitions and lifecycle edges (e.g. what happens at each permitted
  and each seemingly-forbidden transition)
- Discovered API endpoints, each tagged DECLARED_ONLY or OBSERVED_IN_USE
- Client-side functionality relevant to authorization (e.g. JS that hides but
  doesn't actually block privileged UI)

Use available client-side JavaScript inspection and direct HTTP capabilities
(when authorized) to improve the model. Suspicious behavior is not a confirmed
vulnerability at this stage: record it as an unresolved question or a
candidate hypothesis input. A capability found only in a bundle/SDK
(DECLARED_ONLY) is attack surface worth tracking, but must not be treated as
equivalent in confidence to something OBSERVED_IN_USE.

## Phase 5: Security Hypotheses

Continue automatically once attack surface mapping is populated. Search for
paths that might violate an existing invariant or authorization rule. Every
hypothesis records:
- Hypothesis ID
- Invariant or atomic authorization rule being challenged (specific
  Actor x Resource x Action x Condition, not a bundled generalization)
- Relevant actor
- Relevant resource
- Suspected execution path (state whether it relies on a DECLARED_ONLY or
  OBSERVED_IN_USE path)
- Supporting evidence
- Security control that appears missing or uncertain
- Confidence
- Minimal proposed validation method (the smallest, most reversible test that
  would confirm or reject exactly this hypothesis - no more)

### Coverage Review (end of Phase 5, before Validation)

Before moving to Phase 6, systematically review the Security Architecture
Model against the hypotheses generated so far, across:
- Actors (every role/relationship type)
- Resources (every resource type)
- Actions (every distinct action per resource)
- Conditions (ownership, tenant, state-based)
- Tenant boundaries
- Ownership boundaries
- Privileged operations
- State transitions

For each dimension, note whether at least one hypothesis exercises it. Record
any important combination with no corresponding hypothesis as an explicit
**coverage gap** (not silently skipped) - e.g. "no hypothesis challenges
whether a non-owner Admin can Delete another member's resource." Coverage
gaps are not failures; they are scope-limiting facts to report alongside
hypotheses and findings, and candidates for a follow-up engagement.

## Phase 6: Validation

This is the one mandatory pause point in the otherwise autonomous flow. Only
perform active validation when:
1. Explicit authorization to test the target has been provided, and
2. The proposed action is within the stated scope.

When Phases 1-5 have produced hypotheses ready for validation, stop and
present them, then explicitly ask the user to authorize testing and confirm
scope (what's in bounds, e.g. specific test accounts; what's explicitly
excluded, e.g. no destructive writes) before running anything. Do not treat
the original target URL, or the fact that earlier phases proceeded
autonomously, as authorization for active validation - this gate is never
inferred, only explicitly given.

Prefer minimal, reversible tests using test accounts and test data. Avoid
destructive actions when a non-destructive validation is possible. Capture
evidence (exact request/response, screenshot, or extracted content) for every
validation attempt.

**Evidence-scoped confirmation:** a validation result confirms or rejects
*only* the exact edge exercised - the specific actor, resource instance,
action, and condition actually tested. A single successful (or failed) test
must not be used to mark a broader invariant or a bundled rule (e.g. "all
edit/delete permissions") as `CONFIRMED` or `REJECTED` in full. If an
invariant has multiple important edges (e.g. Read vs. Update vs. Delete;
same-org vs. cross-org; own resource vs. another user's resource) and only
some were tested, mark it `PARTIALLY_CONFIRMED` and explicitly list which
edges remain untested/unresolved.

A hypothesis becomes a VALIDATED FINDING (`CONFIRMED`) only when observable
evidence demonstrates the exact edge can be violated. It becomes `REJECTED`
when the exact edge was tested and the control held. Otherwise it stays a
hypothesis or `UNRESOLVED` (evidence gathered so far, not yet decisive).

## Phase 7: Final Output

Once validation (or an explicit decision to stop before it) is complete,
produce a structured report containing:
1. The Security Architecture Model (section A - actors, roles, resources,
   relationships, actions, atomic authorization rules, ownership model,
   tenant/trust boundaries, state machines, observed execution paths,
   invariants, unresolved questions) as a reusable artifact, saved both in
   the narrative Markdown graph and in the structured `security_model.json`
   (see Structured Security Model Output above)
2. Attack surface (with DECLARED_ONLY vs. OBSERVED_IN_USE distinctions)
3. Security hypotheses generated
4. Coverage review and coverage gaps
5. Validation results, with evidence, per hypothesis - using the full status
   vocabulary (CONFIRMED / PARTIALLY_CONFIRMED / REJECTED / UNRESOLVED)
6. Unresolved architecture and coverage questions, consolidated
7. Evidence and confidence for each conclusion

Keep sections 1 (architecture model) and 3-5 (hypotheses/findings) clearly
separated so the architecture model can be reused on its own in a future
analysis stage or engagement.

## Methodology Rules (always apply)

- Evidence before conclusions.
- Never invent architecture: if there's no evidence, mark it an unresolved
  question, not a fact.
- Clearly distinguish observed facts from inference at every step.
- Start from just a target URL; gather everything else (credentials, extra
  roles/tenants, behavior clarifications, constraints, scope details)
  adaptively, only when a concrete point in the analysis needs it, and only
  ask for what that point needs.
- Drive the seven phases forward autonomously; pause only when genuinely
  blocked by missing access, genuine ambiguity, or the Phase 6 authorization
  gate.
- Distinguish capabilities that merely exist in client code/SDKs
  (DECLARED_ONLY) from execution paths actually used by the application
  (OBSERVED_IN_USE); build architecture conclusions on the latter.
- Model authorization atomically (Actor x Resource x Action x Condition); do
  not bundle distinct actions into one invariant without shared evidence.
- Reconstruct lifecycle/state machines for stateful resources as part of the
  architecture, not as an afterthought.
- A validation result confirms only the exact edge tested - use
  PARTIALLY_CONFIRMED when a broader invariant has untested edges.
- Perform the Phase 5 coverage review before validation, and report coverage
  gaps even when no hypothesis was generated for them.
- Do not report an unvalidated hypothesis as a vulnerability.
- Architecture reconstruction always comes before vulnerability hunting.
- Do not use source-code or internal-platform access unless explicitly
  provided as part of the authorized test.
- Prefer behavioral evidence gathered directly from the target application.
- Stay strictly within the authorized target and scope at all times.
- Explicit authorization is mandatory before Phase 6 and is never weakened or
  bypassed by how much of Phases 1-5 ran autonomously.
- Revise earlier inferences when new evidence contradicts them - note what
  changed and why rather than leaving a silent contradiction in the graph.
- Keep `security_model.json` atomic (one action per authorization rule) and
  versioned (`schema_version`), so it can serve as a reliable baseline for a
  future architecture comparison.

## Practical Tool Mapping (generic)

The methodology is tool-agnostic. A typical agent environment needs:

- **Browser automation** (navigate, click, type, read page content,
  screenshot) for UI exploration and UI-driven validation.
- **Direct HTTP client** (e.g. `curl` or a scripting language's HTTP
  library) for endpoint probing when authorized, inspecting client-side
  JavaScript, and producing raw request/response evidence.
- **File read/write** for the persistent Markdown security graph and the
  structured `security_model.json`.

If the environment cannot capture raw network traffic for UI-driven
interactions, evidence for those steps is page content, screenshots, and
extracted text rather than request/response pairs. Use direct HTTP calls
when raw request/response evidence is required, and use them also to
establish whether a path is `OBSERVED_IN_USE` vs. `DECLARED_ONLY`.
