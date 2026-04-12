---
name: cli-skillgen
version: 1.0.0
description: >-
  Generate layered SKILL.md files for a CLI. Use when creating skill files,
  scaffolding skill architecture, or generating documentation for CLI commands.
  Produces shared, resource, helper, recipe, and persona skill layers.
metadata:
  requires:
    skills: ["cli-architect"]
---

# CLI Skill Generator

Generate the complete set of layered SKILL.md files for a CLI. Produces the agent-facing documentation that makes a CLI fully agentic.

## When to Use

- You've built a CLI and need to make it discoverable by AI agents
- You have a feature backlog (from `cli-ideate`) and want skills for each feature
- You have a monolithic SKILL.md and want to split it into layers
- You're adding new commands and need corresponding skill documentation

## Skill Layer Architecture

```
skills/
├── <cli>-shared/SKILL.md        # Auth, flags, output, config — ONE per CLI
├── <cli>-<resource>/SKILL.md    # Per-resource CRUD reference — ONE per resource
├── <cli>-<helper>/SKILL.md      # Per-helper guide — ONE per helper
├── recipe-<workflow>/SKILL.md   # Multi-step agent workflows — ONE per recipe
└── persona-<role>/SKILL.md      # Role-based bundles — ONE per persona
```

## Workflow

### Step 1: Gather CLI Context

If not provided, scan the CLI to understand:
- All commands with flags and descriptions
- Auth mechanism and configuration
- Output format and error handling
- Global flags
- Exit codes

### Step 2: Generate Shared Skill

**Always generate first.** All other skills reference this.

Use the shared skill template from `references/skill-templates.md`.

Content must include:
- Installation instructions
- Authentication setup (full precedence chain)
- Global flags reference table
- CLI syntax pattern: `<cli> <resource> <method> [flags]`
- Output envelope format (success and error)
- Exit codes table
- Security rules (what the agent must never do)

### Step 3: Generate Resource Skills

One per API resource. Use the resource skill template.

Content must include:
- Prerequisite: "Read `../<cli>-shared/SKILL.md` first"
- Command table: method, flags, description
- Examples for common operations
- Helper commands that use this resource
- Discovering more commands: `<cli> <resource> --help`

### Step 4: Generate Helper Skills

One per `+` helper command. Use the helper skill template.

Content must include:
- What workflow this replaces (the multi-step alternative)
- Command signature with all flags
- Example with expected output
- `--dry-run` behavior description

### Step 5: Generate Recipe Skills

One per multi-step agent workflow. Use the recipe skill template.

Content must include:
- Prerequisite: which resource skills to load
- Numbered steps with CLI commands
- Agent reasoning points between steps
- Expected output at each step
- Error handling (what to do if a step fails)

### Step 6: Generate Persona Skills (if applicable)

One per user role. Use the persona skill template.

Content must include:
- Who this persona is for
- Config overlay values
- Modified command behavior
- Recommended helpers and recipes

### Step 7: Validate Size Budgets

Enforce size limits per `skill-creator` standards:

| Skill Type | Max SKILL.md Size | Overflow Strategy |
|-----------|-------------------|-------------------|
| CLI wrapper (shared) | 500 lines | Move auth details to `references/` |
| Resource | 200 lines | Move API details to `references/` |
| Helper | 150 lines | Keep concise — one command, one file |
| Recipe | 300 lines | Move step details to `references/` |
| Persona | 100 lines | Just config overlay + behavior summary |

If a skill exceeds its budget, split heavy content into `references/<topic>.md`.

### Step 8: Validate CSO (Claude Search Optimization)

For each generated skill, verify the `description` field:
- ✅ Starts with triggering conditions ("Use when...")
- ✅ Contains symptoms/keywords an agent would search for
- ✅ Does NOT summarize the workflow (that goes in the body)
- ✅ Under 1024 characters
- ✅ Third person perspective

### Step 9: Present & Gate

Show the file tree and a summary of each generated skill:

```
Generated 12 SKILL.md files:

  skills/
  ├── dining-shared/SKILL.md       (420 lines — auth, flags, output)
  ├── dining-cafes/SKILL.md        (180 lines — cafe CRUD)
  ├── dining-menus/SKILL.md        (195 lines — menu browsing)
  ├── dining-orders/SKILL.md       (160 lines — order management)
  ├── dining-+compare/SKILL.md     (120 lines — side-by-side menus)
  ├── dining-+open-now/SKILL.md    (110 lines — what's open)
  ├── recipe-lunch-advisor/SKILL.md (280 lines — AI lunch recs)
  ├── recipe-weekly-planner/SKILL.md (250 lines — week meal plan)
  ├── recipe-team-lunch/SKILL.md   (230 lines — group coordination)
  ├── persona-health-nut/SKILL.md  (85 lines — calorie-focused)
  ├── persona-speed-demon/SKILL.md (80 lines — fast decisions)
  └── persona-budget-watcher/SKILL.md (75 lines — price-focused)
```

🛑 **STOP GATE** — Review generated skills before writing to disk.

## Common Mistakes

- **Forgetting the shared skill prerequisite.** Every resource/helper skill MUST reference the shared skill. Agents load skills independently — they need to know where auth docs live.
- **Putting workflow details in the description.** The `description` field is for CSO/discovery only. The workflow goes in the SKILL.md body. If you summarize the workflow in the description, Claude will shortcut the full document.
- **Generating skills for unbuilt features.** Skills document what EXISTS, not what's planned. Only generate skills for implemented commands.
- **Exceeding size budgets.** A 500-line SKILL.md wastes context window. Split into body + references.
