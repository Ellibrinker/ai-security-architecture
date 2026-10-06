# Security Architect Agent

This folder contains the actual instructions that drove the Security
Architect agent in the reference engagement (see
[`../examples/`](../examples/)). They are published close to verbatim. The
only changes are removing platform-specific tool names and environment
details.

## Components

| File | Role |
|---|---|
| [`system_prompt.md`](system_prompt.md) | Persistent system prompt. Defines the agent's identity, what it must model (actors, resources, relationships, actions, trust boundaries, invariants), how it records evidence, and the rule that authorization comes before any active testing. |
| [`skills/security-architecture-analysis/SKILL.md`](skills/security-architecture-analysis/SKILL.md) | The engagement skill, loaded at the start of every engagement. It covers the adaptive flow, the seven phases, atomic authorization modeling, execution-path evidence, state machines, the Phase 6 authorization gate, and the `security_model.json` output contract. |
| [`skills/security-architecture-analysis/scripts/run.sh`](skills/security-architecture-analysis/scripts/run.sh) | Skill loader. Prints `SKILL.md` so a skill-capable runtime can inject it into the agent's context. |

## How it runs

1. The runtime loads `system_prompt.md` as the agent's standing instructions.
2. When the user provides a target URL, the agent invokes the skill
   (`run.sh <target-url>`) and follows `SKILL.md`.
3. The agent explores the target with browser automation and, when
   authorized, direct HTTP. It builds a Markdown security graph and a
   `security_model.json` that conforms to
   [`../schema/security_model.schema.json`](../schema/security_model.schema.json).
4. Before any active validation (Phase 6), the agent stops and asks for
   explicit, scoped authorization.

## Validating the output

From the repo root:

```bash
pip install -r requirements.txt
python src/validate_model.py examples/security_model.example.json
```

## Runtime requirements

The agent assumes a runtime that provides:

- an LLM with tool use,
- a skill or instruction loader (any mechanism that puts `SKILL.md` into context),
- browser automation (navigate, click, type, read content, screenshot),
- an HTTP client / shell for raw request-response evidence,
- file read/write for the security graph and model.

No runtime adapter is included yet. Wiring these instructions into a
specific agent framework is listed as future work in the top-level README.
