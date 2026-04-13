# Skill-Building Rules (Extract)

Key rules for ideating CLI skills. Sourced from the Anthropic skill guide and superpowers:skill-creator patterns.

## What a Skill IS

A SKILL.md file that teaches an AI agent **when and how** to compose CLI commands for a specific workflow domain. A skill is agent instructions — not code, not a CLI flag, not middleware.

**Skill:** "Here's how to check your body metrics using garmin-cli" → SKILL.md with commands, examples, triggers
**NOT a skill:** "Add response caching to the HTTP client" → code change to the CLI itself

### Litmus Test

> "Does this need a SKILL.md file to teach an agent a workflow, or is it a code change to the CLI itself?"

- If it teaches an agent **when to use** commands and **how to compose** them → **skill**
- If it adds/modifies CLI source code (flags, middleware, caching, formatters) → **code change** → route to CLI Enhancement Backlog

## Sizing

- Target: 1,500–2,000 words per SKILL.md
- Hard cap: <3,000 words
- If a skill exceeds the cap, split by user intent or move reference tables to `references/`

## Naming Convention

Kebab-case, always prefixed with the CLI name:

| Pattern | When to use | Example |
|---------|-------------|---------|
| `<cli>-shared` | Auth, flags, output format — ONE per CLI | `garmin-shared` |
| `<cli>-<domain>` | Domain grouped by user intent | `garmin-health` |
| `recipe-<workflow>` | Multi-step agent workflow with judgment | `recipe-training-review` |
| `persona-<role>` | Role-based config bundle | `persona-athlete` |

## Trigger Description Format

Every skill needs a trigger description in frontmatter:

```
[What it does] + [Use when...] + [Trigger phrases]
```

Example:
```yaml
description: >-
  Query Garmin health metrics — sleep, heart rate, stress, body battery, SpO2,
  and weight. Use when checking body stats, reviewing sleep quality, or
  monitoring daily health trends. Triggers: "how did I sleep", "heart rate",
  "stress level", "body battery", "weight trend".
```

Include **negative triggers** when the skill could over-match:
```
Do NOT use for: workout scheduling (use garmin-workout), race predictions (use garmin-fitness).
```

## Skill Count Heuristic

Derive skill count from the CLI's API surface area:

| CLI Type | Classification | Target Skills | Naming Pattern |
|----------|---------------|---------------|----------------|
| Multi-service | 3+ distinct API resource groups | 4–8 skills | `<cli>-<domain>` grouped by user intent |
| Single-service | 1–2 resource groups | 2–4 skills | `<cli>-<action>` |
| Single-resource | 1 resource | 1 shared skill | `<cli>-shared` only |

**Count resource groups** from `validated-endpoints.json` — group endpoints by their first path segment after the version prefix.

### Examples

- **garmin-cli** (15+ resource groups: sleep, heartRate, stress, activities, workouts, ...): multi-service → 5–6 skills grouped by intent
- **dining-cli** (2 resource groups: menus, orders): single-service → 2–3 skills
- **uprint-cli** (1 resource: print jobs): single-resource → 1 shared skill

## Progressive Disclosure

Structure each skill for progressive disclosure:
1. **Quick start** — the 2-3 most common commands a user runs daily
2. **Full reference** — complete command table with all flags
3. **Advanced patterns** — piping, scripting, automation recipes

## Clustering by User Intent

Skills group commands by **how users think**, not how the API is organized.

**Wrong** (API surface): one skill per API resource
- `garmin-sleep`, `garmin-heartrate`, `garmin-stress`, `garmin-spo2`, `garmin-weight` (5 skills for related body metrics)

**Right** (user intent): one skill per user question
- `garmin-health` — "How's my body?" (sleep + HR + stress + SpO2 + weight in one skill)

Ask: "What question is the user trying to answer?" Group all commands that answer the same question into one skill.
