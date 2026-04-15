# Feature Ideation Category Framework

> **These categories are brainstorming lenses, NOT the output structure.**
> Use them to think comprehensively about what a CLI could do. Your output
> is organized into **skill domains** (grouped by user intent) and a
> **CLI Enhancement Backlog** (code changes). Do not map categories 1:1
> to skill domains — multiple categories often collapse into a single
> skill domain when they share user intent.

The 7 categories for systematic CLI skill brainstorming. Categories 1-6 inform skill domain identification. Category 7 captures code changes that are explicitly NOT skills.

## Category 1: Daily Workflows

**What:** Commands that users run every single day as part of their routine.

**Pattern:** High-frequency, low-complexity, fast output.

**How to discover:**
- What question does the user ask every day? ("What's for lunch?", "Any new PRs?", "What's my balance?")
- What's the first thing they check in the morning?
- What's the last thing they check before leaving?

**Design rules:**
- Must complete in < 3 seconds
- Must be useful without flags (sensible defaults)
- Should support `--watch` or cron scheduling
- Output should be scannable (not a wall of data)

**Examples:**
- `gh dash` — daily GitHub dashboard
- `az board query --assigned-to @me` — my work items
- `dining now` — what's serving right now

---

## Category 2: New Resource Commands

**What:** CRUD operations for API resources not yet exposed as CLI commands.

**Pattern:** `<cli> <resource> <method> [flags]` — follows REST mapping.

**How to discover:**
- List all API endpoints from recon
- For each unimplemented endpoint, ask: "Would a user ever want to call this directly?"
- Group by resource (orders, balance, stalls, etc.)

**Design rules:**
- One command per resource method (list, get, create, update, delete)
- Always support `--format json` (default) and `--format table`
- Write operations must have `--dry-run` and `--yes`
- List operations must auto-paginate

**REST → CLI mapping:**
| HTTP | CLI | Example |
|------|-----|---------|
| GET /resources | `<cli> resources list` | `dining orders list` |
| GET /resources/{id} | `<cli> resources get <id>` | `dining orders get ORD-123` |
| POST /resources | `<cli> resources create` | `dining cart add --item ITM-456` |
| PUT /resources/{id} | `<cli> resources update <id>` | `dining config set --building 41` |
| DELETE /resources/{id} | `<cli> resources delete <id>` | `dining cart clear` |

---

## Category 3: Helper Commands (+prefix)

**What:** Multi-step workflows collapsed into single commands. These combine 2+ API calls that users typically do together.

**Pattern:** `<cli> +<helper-name> [flags]` — the `+` prefix signals "this is a convenience wrapper."

**Qualification criteria (must meet ALL 3):**
1. Combines 2+ API calls done together
2. 80%+ of users would want this workflow
3. Abstracts away boilerplate (ID resolution, filtering, joining)

**How to discover:**
- What multi-command sequences do users run back-to-back?
- What workflows require copying an ID from one command into another?
- What filtering/sorting do users always do manually?

**Design rules:**
- Must support `--dry-run` (shows all API calls it would make)
- Minimal required flags — sensible defaults for everything
- Output should combine data from all calls into a unified view
- Must also work with `--format json` (flattened or nested output)

**Examples:**
- `gh +release` — create tag + release notes + publish
- `dining +compare cafe1 cafe2` — side-by-side menu comparison
- `dining +open-now` — which cafes are open with time remaining

---

## Category 4: Recipe Skills

**What:** Multi-command workflows documented as SKILL.md files for AI agents to follow. These are NOT CLI commands — they're agent instructions.

**Pattern:** Agent reads the recipe SKILL.md, then executes a sequence of CLI commands with reasoning between steps.

**How to discover:**
- What workflows require JUDGMENT between steps? (e.g., "pick the best option")
- What workflows need context from the user? (e.g., dietary preferences)
- What workflows span multiple resources with decision points?

**Design rules:**
- SKILL.md format with frontmatter (name, description, requires)
- Steps are numbered with CLI commands + expected output
- Agent reasoning points marked with "Evaluate:" or "Decide:"
- Must declare resource skill dependencies in `requires.skills`

**Template:**
```markdown
---
name: recipe-<workflow>
description: "<End-to-end description>"
metadata:
  category: recipe
  requires:
    bins: ["<cli>"]
    skills: ["<cli>-<resource1>", "<cli>-<resource2>"]
---
# <Workflow Name>

## Steps
1. `<cli> <resource1> list --format json` — Get candidates
2. Evaluate: Filter candidates by {criteria}
3. `<cli> <resource2> get {selected_id} --format json` — Get details
4. Decide: Recommend based on {reasoning}
5. Present recommendation to user
```

---

## Category 5: Persona Skills

**What:** Role-based configuration bundles that tailor the CLI experience for specific user types.

**Pattern:** A persona overlays default config and command behavior to match a user role's priorities.

**How to discover:**
- Who are the distinct user types? (e.g., health-conscious eater, busy engineer, team lead)
- What do they optimize for? (speed, health, budget, variety, coordination)
- How would their default flags differ?

**Design rules:**
- Stored in `~/.cli-name/personas/<name>.json`
- Activated via `<cli> config --persona <name>`
- Config overlay merges with base config (persona values win)
- Command defaults override individual command behavior
- Must be completely reversible: `<cli> config --persona none`

**Schema:**
```json
{
  "name": "persona-name",
  "description": "For users who...",
  "configOverlay": { "maxCalories": 600, "sortBy": "calories" },
  "commandDefaults": {
    "now": { "--max-cal": 600 },
    "search": { "--sort": "calories" }
  },
  "enabledHelpers": ["+lowcal", "+nutrition"]
}
```

---

## Category 6: Shared Skills

**What:** Cross-cutting concerns that apply to ALL commands — documented in the `<cli>-shared` SKILL.md.

**Pattern:** Auth, global flags, output format, config, error handling — everything an agent needs to know before using any specific command.

**How to discover:**
- What auth steps must happen before any command works?
- What global flags affect every command? (`--format`, `--yes`, `--dry-run`)
- What output envelope format do all commands share?
- What exit codes does the CLI use?
- What security rules must an agent follow?

**Shared skill contents:**
| Section | What it covers | Example |
|---------|---------------|---------|
| Installation | How to install and configure | `bun install -g gws-cli` |
| Auth | Credential precedence chain | env var → config file → interactive |
| Global flags | Flags available on every command | `--format json/table`, `--yes` |
| Output format | JSON envelope schema | `{ "status": "ok", "data": {...} }` |
| Exit codes | What each code means | 0=success, 1=error, 2=auth |
| Security | What agents must never do | Never store tokens in skill files |

**Note:** The shared skill is always P0 — all other skills depend on it.

---

## Category 7: CLI Enhancement Backlog

**⚠️ Items in this category are NOT skills. They are code changes to the CLI itself.**

**What:** Code improvements — new flags, middleware, caching, formatters, infrastructure. These do NOT become SKILL.md files. They route back to the implementation audit for the next build cycle.

**Pattern:** Changes to CLI source code, not agent instructions.

**How to discover:**
- What filtering do users do AFTER getting output? (→ add a flag)
- What middleware would improve performance? (→ caching, rate limiting)
- What quality gaps did the audit find? (→ infrastructure fixes)
- What config options are missing? (→ env var support)

**Common enhancement types:**
| Type | Examples | NOT a skill because... |
|------|----------|----------------------|
| Flag | `--quiet`, `--output FILE`, `--max-price` | It's a code change to the argument parser |
| Middleware | Response caching, rate limiting | It's a code change to the HTTP client |
| Config | Env var support, config file | It's a code change to the config system |
| Infrastructure | Plugin architecture, watch mode | It's a code change to the CLI framework |
| Quality fix | Error handling, input validation | It's a bug fix or improvement |

**These items go into the "CLI Enhancement Backlog" section of the output, NOT into skill domains.**
