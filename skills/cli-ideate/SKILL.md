---
name: cli-ideate
version: 2.0.0
description: >-
  Identify skill domains for a CLI — groups of commands clustered by user intent
  that each become a SKILL.md file. Use when planning which skills to generate,
  grouping CLI commands into agent-teachable workflows, or deciding how to
  structure skill coverage for a CLI. Produces skill domains with draft triggers
  and a separate CLI enhancement backlog.
metadata:
  requires:
    skills: ["cli-architect"]
---

# CLI Ideate

Identify skill domains — groups of CLI commands clustered by **user intent** — that each become a SKILL.md file. Separates code changes (flags, caching, middleware) into a CLI Enhancement Backlog.

## When to Use

- You've built (or audited) a CLI and want to plan which skills to generate
- You need to group CLI commands into agent-teachable workflow domains
- You want structured ideation that produces skill definitions, not feature lists
- You're deciding how many SKILL.md files a CLI needs and what each one covers

## Inputs

Best results when you provide:
1. **API surface map** (from `api-recon`) — shows what's possible
2. **Existing commands** — shows what's already built
3. **Audit scorecard** (from `cli-audit`) — shows quality gaps
4. **CLI type classification** — multi-service (3+ resource groups), single-service (1-2), or single-resource (1)
5. **Skill guide rules** (from `references/skill-guide-extract.md`) — sizing, naming, triggering constraints

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
6. Count distinct API resource groups (first path segment after version prefix)
```

Also read `references/skill-guide-extract.md` for skill sizing, naming, and counting rules.

### Step 2: Identify Skill Domains

Dispatch **1 general-purpose agent** with full context. A single agent produces better cross-domain coherence than parallel agents.

```prompt
You are a CLI skill architect. Given:
- Service: {name} ({description})
- CLI type: {cli_type} (multi-service | single-service | single-resource)
- Target skill count: {target_count}
- Existing commands: {command_list}
- Unimplemented endpoints: {endpoint_list}
- Data models: {model_summary}
- Audit gaps: {scorecard_summary}
- Skill guide rules: {skill_guide_extract_content}

Identify SKILL DOMAINS — groups of CLI commands clustered by USER INTENT.
Each skill domain will become a SKILL.md file that teaches an AI agent when
and how to compose CLI commands for that workflow.

For each skill domain, provide:
- Skill name (kebab-case: <cli>-shared, <cli>-<domain>, recipe-<workflow>)
- Intent cluster: the user question this skill answers (e.g. "how's my body?")
- Commands covered: which CLI commands belong in this skill
- Draft trigger: "Use when..." description for the SKILL.md frontmatter
- Priority score: impact (1-5) × inverse_effort (1-5) = score

RULES:
- Cluster by how users THINK, not how the API is structured
- "how's my body?" groups sleep + HR + stress + weight, not one skill per API
- Always include a <cli>-shared skill (auth, flags, output format)
- Do NOT propose code changes (caching, new flags, middleware) as skills
- Code changes go into a separate "CLI Enhancement Backlog" section
- Use references/category-framework.md as brainstorming input, NOT as output structure
- Use references/skill-guide-extract.md for sizing and naming rules

Also identify CLI ENHANCEMENT BACKLOG items — code changes that improve
the CLI itself but are NOT skills:
- New global flags (--quiet, --output FILE)
- Middleware (caching, rate limiting)
- Infrastructure (config system, plugin architecture)
- Quality fixes from audit gaps
Label each with type: flag | middleware | config | infrastructure | quality-fix
```

### Step 3: Prioritize & Tier

Rank skill domains by priority score and group into tiers:

| Tier | Criteria | Action |
|------|----------|--------|
| **P0** | Score ≥ 20 or foundational (`<cli>-shared` is always P0) | Generate first |
| **P1** | Score 12-19 | Generate next |
| **P2** | Score 6-11 | Backlog |
| **P3** | Score ≤ 5 | Icebox |

### Step 4: Validate Domain Count

Check against target for CLI type:

| CLI Type | Target | If over target | If under target |
|----------|--------|----------------|-----------------|
| Multi-service (3+ groups) | 4–8 | Merge related domains | Check for missed intent clusters |
| Single-service (2 groups) | 2–4 | You're probably splitting by API, not intent | Likely correct |
| Single-resource (1 group) | 1 | Shared skill only | Shared skill only |

### Step 5: Present & Gate

Present the backlog as a structured summary:

```markdown
## Skill Domains for {cli_name}

CLI type: {cli_type} | Target: {target_count} skills

### P0 — Generate First
| ID | Skill Name | Intent Cluster | Commands Covered | Draft Trigger | Score |
|----|------------|----------------|------------------|---------------|-------|
| 1 | gws-shared | — | all | Auth, flags, output format | 25 |
| 2 | gws-gmail | "Do something with email" | send, list, reply, label, archive | Use when working with Gmail | 20 |
...

### P1 — Generate Next
...

### CLI Enhancement Backlog
| ID | Enhancement | Type | Description |
|----|-------------|------|-------------|
| E1 | Response caching | middleware | Add file-based cache for GET requests |
| E2 | --quiet flag | flag | Suppress non-essential output |
...
```

🛑 **STOP GATE** — User selects which skill domains to generate SKILL.md files for. Enhancement backlog items route to implementation audit, not skill generation.

## Output Artifact

```json
{
  "cli": "cli-name",
  "cli_type": "multi-service|single-service|single-resource",
  "generated": "ISO-timestamp",
  "skill_domains": [
    {
      "id": "cli-domain",
      "name": "cli-domain",
      "intent_cluster": "User question this skill answers",
      "commands_covered": ["cmd1", "cmd2"],
      "draft_trigger": "Use when...",
      "priority": "P0|P1|P2|P3",
      "impact": 5,
      "effort_inverse": 4,
      "score": 20
    }
  ],
  "enhancement_backlog": [
    {
      "id": "enhancement-id",
      "title": "Enhancement Title",
      "type": "flag|middleware|config|infrastructure|quality-fix",
      "description": "What this code change does"
    }
  ],
  "summary": {
    "total_skills": 6,
    "total_enhancements": 8,
    "by_priority": { "P0": 2, "P1": 3, "P2": 1 }
  }
}
```

## Common Mistakes

- **Producing 30+ features instead of 4-8 skill domains.** You're ideating code changes, not skills. A skill is a SKILL.md file — not a flag, cache layer, or formatter.
- **One skill per API resource group.** If you have `gws-gmail-list`, `gws-gmail-send`, `gws-gmail-reply` as separate skills, you're mirroring API structure. Group by service/intent: `gws-gmail` covers all email actions.
- **Code changes in the skill list.** "Response Caching", "--output FILE", "Quiet Mode" are code changes, not skills. Route them to the CLI Enhancement Backlog.
- **Missing the shared skill.** Every CLI needs `<cli>-shared` covering auth, flags, output format. It's always P0.
- **Ignoring the skill guide rules.** Read `references/skill-guide-extract.md` before brainstorming. It has sizing, naming, and counting constraints.
- **Using categories as output structure.** The category framework helps brainstorm comprehensively, but your output is organized by skill domain (user intent), not by category.
