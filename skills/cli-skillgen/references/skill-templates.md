# Skill Templates

Templates for each SKILL.md layer type. Copy, fill placeholders, and customize.

## Shared Skill Template

```markdown
---
name: <cli>-shared
description: >-
  <CLI name> CLI: Shared patterns for authentication, global flags, output formatting,
  and error handling. Read this before using any <cli> resource or helper skill.
  Prerequisite for all <cli>-* skills.
metadata:
  requires:
    bins: ["<cli-binary>"]
---

# <CLI Name> — Shared Reference

## Installation

<Install instructions — npm, pip, brew, or manual>

## Authentication

<Full auth precedence chain:>

| Priority | Source | How to configure |
|----------|--------|-----------------|
| 1 | `<CLI>_TOKEN` env var | `export <CLI>_TOKEN="..."` |
| 2 | Credentials file | `<cli> auth login` → saved to `~/.<cli>/token.json` |
| 3 | Interactive login | Browser-based OAuth/SSO flow |
| 4 | System credential | Azure CLI, gcloud, keyring |

## Global Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--format` | string | `json` | Output format: json, table, yaml, csv |
| `--verbose` | bool | false | Print request/response details to stderr |
| `--dry-run` | bool | false | Show what would happen without executing |
| `--yes` | bool | false | Skip confirmation prompts |
| `--force` | bool | false | Skip confirmation AND overwrite protection |
| `--no-cache` | bool | false | Bypass response cache |
| `--quiet` | bool | false | Suppress non-essential output |

## CLI Syntax

\`\`\`
<cli> <resource> <method> [flags]
<cli> +<helper> [flags]
\`\`\`

## Output Format

### Success
\`\`\`json
{ "status": "success", "data": { ... }, "metadata": { "command": "...", "timestamp": "..." } }
\`\`\`

### Error
\`\`\`json
{ "status": "error", "error": { "code": 1, "type": "api_error", "message": "..." } }
\`\`\`

## Exit Codes

| Code | Name | Meaning |
|------|------|---------|
| 0 | SUCCESS | Command completed successfully |
| 1 | API_ERROR | API returned 4xx/5xx |
| 2 | AUTH_ERROR | Authentication failed |
| 3 | VALIDATION_ERROR | Invalid input/flags |
| 4 | NOT_FOUND | Resource not found |
| 5 | INTERNAL_ERROR | Unexpected CLI error |

## Security Rules

- NEVER log tokens, passwords, or API keys
- NEVER include auth headers in --verbose output
- ALWAYS use --dry-run before destructive operations
- ALWAYS confirm before delete/overwrite unless --yes/--force
```

---

## Resource Skill Template

```markdown
---
name: <cli>-<resource>
description: >-
  <Service>: <What this resource represents and common operations>.
  Use when user asks about <resource> management: listing, viewing, creating,
  updating, or deleting <resource> records.
metadata:
  requires:
    bins: ["<cli-binary>"]
    cliHelp: "<cli> <resource> --help"
---

# <Resource Name>

> Prerequisite: Read `../<cli>-shared/SKILL.md` for auth and global flags.

## Commands

| Method | Command | Description |
|--------|---------|-------------|
| List | `<cli> <resource> list [--page-size N]` | List all <resources> |
| Get | `<cli> <resource> get <id>` | Get <resource> details |
| Create | `<cli> <resource> create --name "..." [--dry-run]` | Create new <resource> |
| Delete | `<cli> <resource> delete <id> [--yes]` | Delete a <resource> |

## Examples

\`\`\`bash
# List all
<cli> <resource> list --format table

# Get by ID
<cli> <resource> get RES-123

# Create with dry-run
<cli> <resource> create --name "Test" --dry-run
\`\`\`

## Related Helpers

- `<cli> +<helper>` — <what it does with this resource>

## Discovering Commands

\`\`\`bash
<cli> <resource> --help
\`\`\`
```

---

## Helper Skill Template

```markdown
---
name: <cli>-<helper>
description: >-
  <What workflow this helper replaces>. Combines <resource1> + <resource2> into
  a single command. Use when user wants to <goal> without running multiple commands.
metadata:
  requires:
    bins: ["<cli-binary>"]
    skills: ["<cli>-<resource1>", "<cli>-<resource2>"]
---

# +<helper-name>

> Prerequisite: Read `../<cli>-shared/SKILL.md` for auth and global flags.

## What It Replaces

Without this helper:
\`\`\`bash
<cli> <resource1> list --format json | jq '.data[0].id'
<cli> <resource2> get <id-from-above> --format json
# Manual comparison/filtering
\`\`\`

With this helper:
\`\`\`bash
<cli> +<helper> [flags]
\`\`\`

## Usage

\`\`\`bash
<cli> +<helper> [--flag1 value] [--flag2 value]
\`\`\`

## Flags

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| ... | ... | ... | ... |

## Example

\`\`\`bash
<cli> +<helper> --flag1 value
\`\`\`

## Dry Run

\`\`\`bash
<cli> +<helper> --dry-run
# Shows: Would call GET /api/v2/resource1, then GET /api/v2/resource2/{id}
\`\`\`
```

---

## Recipe Skill Template

```markdown
---
name: recipe-<workflow-name>
description: >-
  <End-to-end description of what this recipe accomplishes>.
  Use when user asks to <goal phrase> or needs <outcome>.
metadata:
  category: recipe
  requires:
    bins: ["<cli-binary>"]
    skills: ["<cli>-<resource1>", "<cli>-<resource2>"]
---

# <Workflow Name>

> Prerequisite: Load skills: `<cli>-<resource1>`, `<cli>-<resource2>`

## When to Use

<1-2 sentences describing the triggering scenario>

## Steps

### 1. Gather context
\`\`\`bash
<cli> config --format json    # Get user settings
\`\`\`

### 2. Fetch candidates
\`\`\`bash
<cli> <resource1> list --format json    # Get available options
\`\`\`

### 3. Evaluate
**Agent reasoning:** Filter candidates by {criteria}. Consider {factors}.
Select the best {N} options based on {scoring}.

### 4. Get details
\`\`\`bash
<cli> <resource2> get {selected_id} --format json    # Deep dive
\`\`\`

### 5. Present recommendation
Format the recommendation with:
- Why this option was chosen
- Key details (price, time, location)
- Alternative options if the user doesn't like the pick

## Error Handling

- If Step 2 returns empty: inform user no options available, suggest broadening criteria
- If Step 4 fails with exit code 4: selected item no longer available, retry with next candidate
```

---

## Persona Skill Template

```markdown
---
name: persona-<role>
description: >-
  <CLI name> persona for <role description>. Optimizes for <what this role cares about>.
  Use when user identifies as a <role> or asks for <role>-optimized defaults.
metadata:
  category: persona
  requires:
    bins: ["<cli-binary>"]
    skills: ["<cli>-shared"]
---

# Persona: <Role Name>

## Who This Is For

<1-2 sentences describing the target user>

## Config Overlay

\`\`\`bash
<cli> config --persona <role>
\`\`\`

Applies these defaults:
\`\`\`json
{
  "<setting1>": "<value>",
  "<setting2>": "<value>"
}
\`\`\`

## Modified Command Behavior

| Command | Default Behavior | With Persona |
|---------|-----------------|-------------|
| `<cli> <cmd1>` | Shows all items | Filters to <criteria> |
| `<cli> <cmd2>` | Sorts by name | Sorts by <priority> |

## Recommended Workflows

- `<cli> +<helper1>` — <why this helper fits the persona>
- `recipe-<workflow>` — <why this recipe fits>

## Deactivate

\`\`\`bash
<cli> config --persona none
\`\`\`
```
