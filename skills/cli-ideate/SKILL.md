---
name: cli-ideate
version: 1.0.0
description: >-
  Brainstorm features for a CLI across 6 categories. Use when ideating CLI commands,
  planning CLI features, building a feature backlog, or deciding what to build next.
  Produces prioritized backlog with dependency mapping.
metadata:
  requires:
    skills: ["cli-architect"]
---

# CLI Ideate

Systematic feature brainstorming across 6 categories. Produces a prioritized backlog with dependency mapping.

## When to Use

- You've built (or audited) a CLI and want to plan what's next
- You have unimplemented API endpoints and need to decide what to build
- You want structured ideation, not just a random feature list
- You're planning a sprint or roadmap for a CLI project

## Inputs

Best results when you provide:
1. **API surface map** (from `api-recon`) — shows what's possible
2. **Existing commands** — shows what's already built
3. **Audit scorecard** (from `cli-audit`) — shows quality gaps that unlock features

Can also run standalone with just a CLI codebase path.

## Workflow

### Step 1: Build Context

If inputs aren't provided, gather them:

```prompt
Explore the CLI at {path}. Report:
1. Every implemented command with flags and what it does
2. Every API endpoint called (method, URL, which command uses it)
3. Every type/model defined (data shapes available)
4. Known unimplemented endpoints (defined in client but not in commands)
5. The service's domain — what real-world problem does this CLI solve?
```

### Step 2: Brainstorm Across 6 Categories

Dispatch **1 general-purpose agent** with full context. A single agent produces better cross-category coherence than parallel agents.

```prompt
You are a CLI product architect. Given:
- Service: {name} ({description})
- Existing commands: {command_list}
- Unimplemented endpoints: {endpoint_list}
- Data models: {model_summary}
- Audit gaps: {scorecard_summary}

Brainstorm features across ALL 6 categories. For each feature, provide:
- ID (kebab-case)
- Title
- Category (one of the 6)
- Description (1-2 sentences, specific enough to implement)
- Commands/endpoints used
- Priority score: impact (1-5) × inverse_effort (1-5) = score
- Dependencies on other features

Categories (see references/category-framework.md):
1. Daily Workflows — commands users run every day
2. New Resource Commands — CRUD for unimplemented API resources
3. Helper Commands (+prefix) — multi-step workflows as single commands
4. Recipe Skills — SKILL.md-driven multi-command agent workflows
5. Persona Skills — role-based configuration bundles
6. Global Enhancements — cross-cutting improvements (flags, filters, formatters)

Generate at least 5 ideas per category. Be creative but practical.
Think about the user's REAL daily workflow with this service.
```

### Step 3: Prioritize & Tier

Rank all features by priority score and group into tiers:

| Tier | Criteria | Action |
|------|----------|--------|
| **P0** | Score ≥ 20 or foundation dependency | Build immediately |
| **P1** | Score 12-19 | Next sprint |
| **P2** | Score 6-11 | Backlog |
| **P3** | Score ≤ 5 | Icebox |

### Step 4: Map Dependencies

Identify which features depend on others:

```
Feature A → requires Feature B
Meal log → enables: recommendations, spending tracker, weekly planner
Balance command → enables: budget optimizer, spending report
```

### Step 5: Present & Gate

Present the backlog as a structured summary:

```markdown
## Feature Backlog: {cli_name}

### Summary
- {total} features across 6 categories
- {p0_count} P0, {p1_count} P1, {p2_count} P2, {p3_count} P3

### P0 — Ship First
| ID | Title | Category | Impact | Effort | Score |
|----|-------|----------|--------|--------|-------|
| balance-cmd | Meal card balance | resource | 5 | 5 | 25 |
...

### Dependency Graph
feature-a → feature-b → feature-c
                      → feature-d
```

🛑 **STOP GATE** — User selects which items to proceed with. Unselected items remain in backlog.

## Output Artifact

```json
{
  "cli": "cli-name",
  "generated": "ISO-timestamp",
  "features": [
    {
      "id": "feature-id",
      "title": "Feature Title",
      "category": "daily-workflow|resource|helper|recipe|persona|global",
      "description": "What this feature does",
      "priority": "P0|P1|P2|P3",
      "impact": 5,
      "effort_inverse": 4,
      "score": 20,
      "endpoints_used": ["/api/v2/..."],
      "depends_on": ["other-feature-id"],
      "acceptance_criteria": ["Criterion 1", "Criterion 2"]
    }
  ],
  "summary": {
    "total": 34,
    "by_category": { "daily-workflow": 3, "resource": 8, "helper": 10, "recipe": 6, "persona": 5, "global": 2 },
    "by_priority": { "P0": 4, "P1": 10, "P2": 12, "P3": 8 }
  }
}
```

## Common Mistakes

- **Ideating without the API surface.** You'll miss features that unimplemented endpoints unlock. Always run recon first if possible.
- **All features in one category.** If you only generated resource commands, you missed workflows, helpers, and personas. Push for diversity.
- **Ignoring the dependency graph.** A "meal log" feature might be foundational — many features depend on it. Prioritize foundations.
- **Confusing helpers and recipes.** Helpers are deterministic CLI commands (+ prefix). Recipes are SKILL.md instructions for agents. Different audiences.
