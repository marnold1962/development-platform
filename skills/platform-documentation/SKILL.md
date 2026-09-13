---
name: platform-documentation
description: Where and how platform projects keep documentation — docs/specs for stories and requirements, DECISIONS.md, CHANGES.md, and when to update each. Use when work changes a requirement, story, decision or behaviour.
---

# Documentation on the platform

- `docs/specs/<name>.md` — one spec per feature: story, acceptance criteria, `status: draft | agreed | built`.
- `docs/DECISIONS.md` — append-only: `## YYYY-MM-DD — <decision>` then the reason.
- `docs/CHANGES.md` — newest first: date, change, spec or requirement affected.
- Update when an implementation meaningfully changes a requirement, story, architecture or database behaviour. Not for cosmetic changes.
- Never invent a requirement. Unspecified behaviour becomes a question in the spec.
- Specs live in the repository they describe.
