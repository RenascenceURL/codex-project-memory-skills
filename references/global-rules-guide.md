# Global Rules Guide

Use this guide when drafting or revising `GLOBAL_ENGINEERING_RULES.md`.
Keep each rule short, testable, and easy to apply during implementation.

## Suggested Categories

1. Coding preferences
2. Architecture preferences
3. Workflow rules
4. Communication preferences
5. Hard constraints

## Rule Writing Format

Use one-line imperative statements:

- "Write tests for every bug fix."
- "Prefer explicit dependencies over hidden globals."
- "Call out uncertainty before implementation when assumptions are high risk."

Avoid abstract preferences that cannot influence concrete coding decisions.

## Examples by Category

### Coding preferences

- Prefer small functions with clear naming.
- Avoid introducing new dependencies without a reason.
- Keep error messages actionable.

### Architecture preferences

- Keep business logic framework-agnostic.
- Enforce module boundaries and limit cross-layer imports.
- Prefer composition patterns for extensibility.

### Workflow rules

- Start sessions by summarizing prior context and next action.
- Record decisions that change APIs or data shape.
- End sessions with a handoff entry.

### Communication preferences

- Provide findings before summaries in reviews.
- Include file paths and line references for bugs.
- State assumptions and residual risk explicitly.

### Hard constraints

- Do not run destructive commands without explicit user approval.
- Preserve unrelated local changes.
- Do not bypass CI checks without user confirmation.
