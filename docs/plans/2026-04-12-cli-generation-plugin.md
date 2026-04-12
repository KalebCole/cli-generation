# cli-generation Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code plugin that autonomously generates complete, tested, audited CLIs with skills from any API surface description.

**Architecture:** A Claude Code plugin with 1 command (orchestrator), 9 agents (one per pipeline phase), and 6 standalone skills (4 ported from cli-toolkit-skills, 2 new). The orchestrator dispatches subagents sequentially, each reading/writing to a shared workspace. No approval gates between phases except auth fallback and skill ideation pause.

**Tech Stack:** Claude Code plugin (markdown-based: commands, agents, skills). One bash script for GitHub push. All content is SKILL.md / agent .md / command .md files with YAML frontmatter.

**Source repo:** KalebCole/cli-toolkit-skills (existing skills to port)
**Target repo:** New repo for the plugin (created during Task 1)

---

### Task 1: Scaffold Plugin Structure + Manifest

**Files:**
- Create: `cli-generation/.claude-plugin/plugin.json`
- Create: `cli-generation/README.md`

- [ ] **Step 1: Create the plugin repo directory**

```bash
mkdir -p ~/repos/cli-generation/.claude-plugin
mkdir -p ~/repos/cli-generation/commands
mkdir -p ~/repos/cli-generation/agents
mkdir -p ~/repos/cli-generation/skills/cli-auth-recon
mkdir -p ~/repos/cli-generation/skills/cli-api-recon
mkdir -p ~/repos/cli-generation/skills/cli-architect/references
mkdir -p ~/repos/cli-generation/skills/cli-audit/references
mkdir -p ~/repos/cli-generation/skills/cli-ideate/references
mkdir -p ~/repos/cli-generation/skills/cli-skillgen/references
mkdir -p ~/repos/cli-generation/scripts
```

- [ ] **Step 2: Write plugin.json manifest**

Write to `cli-generation/.claude-plugin/plugin.json`:

```json
{
  "name": "cli-generation",
  "version": "1.0.0",
  "description": "Autonomous CLI generation from any API surface. 10-phase subagent pipeline: auth recon, API mapping, validation, architecture, audit, TDD generation, skill creation.",
  "author": {
    "name": "Kaleb Cole"
  },
  "repository": "https://github.com/KalebCole/cli-generation",
  "license": "MIT",
  "keywords": ["cli", "generation", "api", "automation", "tdd", "subagent"]
}
```

- [ ] **Step 3: Write README.md**

Write to `cli-generation/README.md` with: plugin overview, install instructions (`/install github:KalebCole/cli-generation`), what users get (1 command, 6 skills, 9 internal agents), pipeline diagram (text), link to spec.

- [ ] **Step 4: Initialize git repo**

```bash
cd ~/repos/cli-generation
git init
git add .
git commit -m "chore: scaffold plugin structure and manifest"
```

---

### Task 2: Port cli-architect Skill

**Files:**
- Create: `cli-generation/skills/cli-architect/SKILL.md`

- [ ] **Step 1: Read source skill**

Read `/c/repos/cli-toolkit-skills/skills/cli-architect/SKILL.md` (814 lines).

- [ ] **Step 2: Port SKILL.md**

Copy the content to `cli-generation/skills/cli-architect/SKILL.md`. Update the frontmatter:

```yaml
---
name: cli-architect
version: 1.0.0
description: >-
  Design a CLI from an API spec. Use when designing a new CLI, scaffolding CLI architecture,
  wrapping an API, or creating command-line tools. Produces command trees, flag contracts,
  JSON output schemas, auth design, HTTP module design, and skill architecture.
metadata:
  requires:
    skills: []
---
```

Keep all content as-is. No path updates needed — skills reference patterns, not file paths.

- [ ] **Step 3: Verify frontmatter parses**

Confirm the YAML frontmatter is valid (no tabs, proper indentation, description doesn't contain unescaped colons).

- [ ] **Step 4: Commit**

```bash
cd ~/repos/cli-generation
git add skills/cli-architect/
git commit -m "feat: port cli-architect skill from cli-toolkit-skills"
```

---

### Task 3: Port cli-audit Skill + References

**Files:**
- Create: `cli-generation/skills/cli-audit/SKILL.md`
- Create: `cli-generation/skills/cli-audit/references/quality-checklist.md`

- [ ] **Step 1: Read source files**

Read `/c/repos/cli-toolkit-skills/skills/cli-audit/SKILL.md` (117 lines) and `/c/repos/cli-toolkit-skills/skills/cli-audit/references/quality-checklist.md` (154 lines).

- [ ] **Step 2: Port SKILL.md**

Copy to `cli-generation/skills/cli-audit/SKILL.md`. Update frontmatter:

```yaml
---
name: cli-audit
version: 1.0.0
description: >-
  Grade a CLI against 14-point quality checklist. Use when auditing CLI quality,
  evaluating agentic readiness, grading an existing CLI, or running a CLI scorecard.
  Produces letter grade, category breakdown, gap analysis, and remediation backlog.
metadata:
  requires:
    skills: ["cli-architect"]
---
```

- [ ] **Step 3: Port quality-checklist.md**

Copy `/c/repos/cli-toolkit-skills/skills/cli-audit/references/quality-checklist.md` to `cli-generation/skills/cli-audit/references/quality-checklist.md`. No changes needed.

- [ ] **Step 4: Commit**

```bash
cd ~/repos/cli-generation
git add skills/cli-audit/
git commit -m "feat: port cli-audit skill with quality checklist reference"
```

---

### Task 4: Port cli-ideate Skill + References

**Files:**
- Create: `cli-generation/skills/cli-ideate/SKILL.md`
- Create: `cli-generation/skills/cli-ideate/references/category-framework.md`

- [ ] **Step 1: Read source files**

Read `/c/repos/cli-toolkit-skills/skills/cli-ideate/SKILL.md` (161 lines) and `/c/repos/cli-toolkit-skills/skills/cli-ideate/references/category-framework.md` (184 lines).

- [ ] **Step 2: Port SKILL.md**

Copy to `cli-generation/skills/cli-ideate/SKILL.md`. Update frontmatter:

```yaml
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
```

- [ ] **Step 3: Port category-framework.md**

Copy to `cli-generation/skills/cli-ideate/references/category-framework.md`. No changes needed.

- [ ] **Step 4: Commit**

```bash
cd ~/repos/cli-generation
git add skills/cli-ideate/
git commit -m "feat: port cli-ideate skill with category framework reference"
```

---

### Task 5: Port cli-skillgen Skill + References

**Files:**
- Create: `cli-generation/skills/cli-skillgen/SKILL.md`
- Create: `cli-generation/skills/cli-skillgen/references/skill-templates.md`

- [ ] **Step 1: Read source files**

Read `/c/repos/cli-toolkit-skills/skills/cli-skillgen/SKILL.md` (156 lines) and `/c/repos/cli-toolkit-skills/skills/cli-skillgen/references/skill-templates.md` (313 lines).

- [ ] **Step 2: Port SKILL.md**

Copy to `cli-generation/skills/cli-skillgen/SKILL.md`. Update frontmatter:

```yaml
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
```

- [ ] **Step 3: Port skill-templates.md**

Copy to `cli-generation/skills/cli-skillgen/references/skill-templates.md`. No changes needed.

- [ ] **Step 4: Commit**

```bash
cd ~/repos/cli-generation
git add skills/cli-skillgen/
git commit -m "feat: port cli-skillgen skill with skill templates reference"
```

---

### Task 6: Write cli-auth-recon Skill (NEW)

**Files:**
- Create: `cli-generation/skills/cli-auth-recon/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

Write to `cli-generation/skills/cli-auth-recon/SKILL.md`:

```yaml
---
name: cli-auth-recon
version: 1.0.0
description: >-
  Discover authentication mechanism for an API. Use when figuring out how an API authenticates,
  what auth type a service uses, discovering OAuth2 endpoints, checking for API keys,
  or preparing to wrap an authenticated API in a CLI.
metadata:
  requires:
    skills: []
---
```

Then write the skill body covering:

**Section 1: When to Use** — Trigger keywords and scenarios.

**Section 2: Resolution Order** — The 5-step autonomous discovery order:
1. Edge browser profile cookies via CDP
2. Env vars, config files, keyrings
3. OpenAPI securitySchemes parsing
4. Cloud provider configs (~/.aws/, ~/.azure/, ~/.kube/)
5. Unauthenticated probe

**Section 3: Supported Auth Types** — The full 11-type table from the spec (bearer, API key, cookie, basic, OAuth2 manual flow, AWS SigV4, Azure AD, mTLS, custom headers, SAML, no auth). For each: what to look for, how to detect, whether it's automated.

**Section 4: OAuth2 Manual Flow** — Detail the gogcli-inspired pattern:
1. Discover OAuth2 endpoints (OpenAPI securitySchemes, .well-known/openid-configuration)
2. Generate auth URL with correct scopes
3. Present URL to user (they open in any browser)
4. User pastes redirect URL back
5. Extract auth code, exchange for tokens
6. Store refresh token reference in auth-profile.json (NOT the token itself)
7. Document auto-refresh mechanism for generated CLI

**Section 5: Auth Profile Output** — The auth-profile.json schema. Emphasize: NEVER store actual secrets. Only mechanism + credential source references.

**Section 6: Fallback** — When autonomous fails, write auth-blocked.json with exactly what's needed. Let the orchestrator handle the user prompt.

- [ ] **Step 2: Verify skill structure**

Confirm: frontmatter parses, description starts with trigger keywords, progressive disclosure (summary up top, detail below), under 400 lines.

- [ ] **Step 3: Commit**

```bash
cd ~/repos/cli-generation
git add skills/cli-auth-recon/
git commit -m "feat: add cli-auth-recon skill — 11 auth type discovery"
```

---

### Task 7: Write cli-api-recon Skill (NEW)

**Files:**
- Create: `cli-generation/skills/cli-api-recon/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

Write to `cli-generation/skills/cli-api-recon/SKILL.md`:

```yaml
---
name: cli-api-recon
version: 1.0.0
description: >-
  Map an API surface — endpoints, schemas, rate limits, pagination patterns.
  Use when exploring an API, reverse-engineering endpoints, parsing OpenAPI specs,
  mapping a GraphQL schema, discovering gRPC methods, or preparing API data for CLI generation.
metadata:
  requires:
    skills: []
---
```

Then write the skill body covering:

**Section 1: When to Use** — Trigger keywords and scenarios.

**Section 2: Strategy by Input Type** — The 4-row strategy table from the spec:
- Docs available → parse first
- Docs + running service → parse then probe for undocumented
- Running service only → reverse engineer (crawl, probe, CDP network sniffing)
- Raw endpoint list → validate and enrich

**Section 3: Endpoint Discovery Methods** — For each input type, the specific techniques:
- OpenAPI: parse paths, schemas, parameters, securitySchemes
- GraphQL: introspection query, extract queries/mutations/subscriptions
- gRPC: parse .proto files, extract services/methods/message types
- Web URL: crawl, look for /api/, /v1/, /graphql, check network tab via CDP
- SDK: extract public API surface from docs/type definitions

**Section 4: Output Schema** — The endpoints.json format from the spec. Each endpoint: method, path, description, params, response_schema, pagination, auth_required. Plus models, rate_limits, coverage stats.

**Section 5: Enrichment** — After initial discovery, probe endpoints to capture:
- Actual response schemas (validate against documented)
- Pagination patterns (cursor, offset, page token)
- Rate limit headers
- Error response formats
- Response times

- [ ] **Step 2: Verify skill structure**

Confirm: frontmatter parses, description has trigger keywords, under 400 lines.

- [ ] **Step 3: Commit**

```bash
cd ~/repos/cli-generation
git add skills/cli-api-recon/
git commit -m "feat: add cli-api-recon skill — API surface mapping"
```

---

### Task 8: Write Agent Definitions (Phases 1-3: Recon Agents)

**Files:**
- Create: `cli-generation/agents/auth-recon.md`
- Create: `cli-generation/agents/api-recon.md`
- Create: `cli-generation/agents/endpoint-validator.md`

- [ ] **Step 1: Write auth-recon agent**

Write to `cli-generation/agents/auth-recon.md`:

```yaml
---
description: >-
  Auth recon subagent for the cli-generation pipeline. Discovers authentication mechanisms
  for an API. Reads input-classification.json, writes auth-profile.json. Never stores
  actual secrets — only mechanism descriptions and credential source references.
tools:
  - Read
  - Write
  - Bash
  - WebFetch
  - AskUserQuestion
  - Glob
  - Grep
---
```

Body instructions:
1. Read `.cli-pipeline/input-classification.json` to understand the input type
2. Invoke the `cli-auth-recon` skill
3. Follow the 5-step resolution order
4. Write `.cli-pipeline/auth-profile.json` with mechanism + credential source (NO secrets)
5. If blocked: write `.cli-pipeline/auth-blocked.json` with what you need, then use AskUserQuestion to ask the user for credentials info (not the actual secret — the source/location)
6. After getting user input, retry and write auth-profile.json

- [ ] **Step 2: Write api-recon agent**

Write to `cli-generation/agents/api-recon.md`:

```yaml
---
description: >-
  API recon subagent for the cli-generation pipeline. Maps all available API endpoints,
  schemas, and metadata. Reads input-classification.json and auth-profile.json,
  writes endpoints.json. Parses docs first, reverse-engineers only when needed.
tools:
  - Read
  - Write
  - Bash
  - WebFetch
  - Glob
  - Grep
---
```

Body instructions:
1. Read `.cli-pipeline/input-classification.json` and `.cli-pipeline/auth-profile.json`
2. Invoke the `cli-api-recon` skill
3. Choose strategy based on input type (parse docs vs reverse engineer)
4. Use auth mechanism from auth-profile.json when probing endpoints
5. Write `.cli-pipeline/endpoints.json` in the schema defined by the skill

- [ ] **Step 3: Write endpoint-validator agent**

Write to `cli-generation/agents/endpoint-validator.md`:

```yaml
---
description: >-
  Endpoint validator subagent for the cli-generation pipeline. Hits every discovered
  endpoint with valid auth, confirms responses match schemas, flags dead/broken routes.
  Reads auth-profile.json and endpoints.json, writes validated-endpoints.json.
tools:
  - Read
  - Write
  - Bash
  - WebFetch
---
```

Body instructions:
1. Read `.cli-pipeline/auth-profile.json` and `.cli-pipeline/endpoints.json`
2. For each endpoint: send test request using auth mechanism, verify response code + schema
3. Record per-endpoint: validation_status, response_time_ms, actual_response_code, schema_match
4. Write `.cli-pipeline/validated-endpoints.json`

- [ ] **Step 4: Commit**

```bash
cd ~/repos/cli-generation
git add agents/auth-recon.md agents/api-recon.md agents/endpoint-validator.md
git commit -m "feat: add recon agents — auth, api, endpoint validator"
```

---

### Task 9: Write Agent Definitions (Phases 4-5: Architect + Audit)

**Files:**
- Create: `cli-generation/agents/cli-architect.md`
- Create: `cli-generation/agents/architecture-auditor.md`

- [ ] **Step 1: Write cli-architect agent**

Write to `cli-generation/agents/cli-architect.md`:

```yaml
---
description: >-
  CLI architect subagent for the cli-generation pipeline. Designs the full CLI architecture
  from validated endpoints. Reads validated-endpoints.json and auth-profile.json,
  writes architecture.md to the CLI repo's docs/ directory. Invokes the cli-architect skill.
tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
---
```

Body instructions:
1. Read `.cli-pipeline/validated-endpoints.json` and `.cli-pipeline/auth-profile.json`
2. Read `.cli-pipeline/input-classification.json` for tech stack choice
3. Invoke the `cli-architect` skill — follow the 3-phase workflow (Triage → Architect → Build)
4. Skip Triage Step 1.2 (API discovery) — use validated-endpoints.json instead
5. Include auth commands (login, logout, status, whoami) based on auth-profile.json
6. Write architecture.md to the CLI repo path from input-classification.json: `<repo_path>/docs/architecture.md`

- [ ] **Step 2: Write architecture-auditor agent**

Write to `cli-generation/agents/architecture-auditor.md`:

```yaml
---
description: >-
  Architecture auditor subagent for the cli-generation pipeline. Grades CLI architecture
  against the 14-point quality checklist. Reads architecture.md, writes arch-audit.md.
  If grade < B, provides specific findings for the architect to fix.
tools:
  - Read
  - Write
  - Glob
  - Grep
---
```

Body instructions:
1. Read `<cli-repo>/docs/architecture.md`
2. Invoke the `cli-audit` skill against the architecture document
3. Grade A-F using the 14-point quality checklist
4. Write `<cli-repo>/docs/arch-audit.md` with: grade, category breakdown, specific findings, remediation items
5. If grade < B: clearly list what needs fixing (the orchestrator will dispatch the architect agent again with these findings)

- [ ] **Step 3: Commit**

```bash
cd ~/repos/cli-generation
git add agents/cli-architect.md agents/architecture-auditor.md
git commit -m "feat: add architect and architecture auditor agents"
```

---

### Task 10: Write Agent Definitions (Phase 6-7: Generate + Audit Implementation)

**Files:**
- Create: `cli-generation/agents/cli-generator.md`
- Create: `cli-generation/agents/implementation-auditor.md`

- [ ] **Step 1: Write cli-generator agent**

Write to `cli-generation/agents/cli-generator.md`:

```yaml
---
description: >-
  CLI generator subagent for the cli-generation pipeline. The big phase — actually writes
  the CLI code using TDD. Reads architecture.md and validated-endpoints.json.
  Writes src/, tests/, package.json to the CLI repo. Must invoke superpowers:test-driven-development
  and superpowers:verification-before-completion.
tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---
```

Body instructions:
1. Read `<cli-repo>/docs/architecture.md` for the full CLI design
2. Read `.cli-pipeline/validated-endpoints.json` for endpoint details
3. Read `.cli-pipeline/input-classification.json` for tech stack (typescript/python/powershell/custom)
4. **MUST invoke** `superpowers:test-driven-development` — follow TDD cycle for every feature
5. Scaffold project based on tech stack:
   - TypeScript: Commander.js + Vitest + tsup, `package.json`
   - Python: Click + pytest + uv, `pyproject.toml`
   - PowerShell: Native module + Pester, `.psd1`
6. Implement in this order: core lib (http, auth, output) → base commands (CRUD) → helpers → auth commands
7. **MUST invoke** `superpowers:verification-before-completion` — all tests pass, CLI builds and runs
8. Write to `<cli-repo>/src/`, `<cli-repo>/tests/`, `<cli-repo>/package.json` (or equivalent)

If this agent receives an `audit-findings` parameter (from the Phase 7 loop), read `<cli-repo>/docs/impl-audit.md` and make targeted fixes to the existing code. Do NOT regenerate — only fix what the audit identified.

- [ ] **Step 2: Write implementation-auditor agent**

Write to `cli-generation/agents/implementation-auditor.md`:

```yaml
---
description: >-
  Implementation auditor subagent for the cli-generation pipeline. Grades the built CLI
  against the 14-point quality checklist. Reads the CLI repo codebase, writes impl-audit.md.
  If grade < B, provides specific findings for targeted fixes.
tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
---
```

Body instructions:
1. Read the full CLI repo at `<cli-repo>/`
2. Invoke the `cli-audit` skill against the actual codebase (not just the architecture doc)
3. Run the CLI's test suite to verify tests pass
4. Grade A-F using the 14-point quality checklist
5. Write `<cli-repo>/docs/impl-audit.md` with: grade, category breakdown, specific code-level findings
6. If grade < B: list specific fixes needed (e.g., "add --dry-run to delete command in src/commands/users.ts:45")

- [ ] **Step 3: Commit**

```bash
cd ~/repos/cli-generation
git add agents/cli-generator.md agents/implementation-auditor.md
git commit -m "feat: add CLI generator (TDD) and implementation auditor agents"
```

---

### Task 11: Write Agent Definitions (Phases 8-9: Ideate + Skillgen)

**Files:**
- Create: `cli-generation/agents/skill-ideator.md`
- Create: `cli-generation/agents/skill-generator.md`

- [ ] **Step 1: Write skill-ideator agent**

Write to `cli-generation/agents/skill-ideator.md`:

```yaml
---
description: >-
  Skill ideation subagent for the cli-generation pipeline. Brainstorms skill features
  across 6 categories using the cli-ideate methodology. Reads validated-endpoints.json,
  architecture.md, and impl-audit.md. Writes feature-backlog.md.
tools:
  - Read
  - Write
  - Glob
  - Grep
---
```

Body instructions:
1. Read `.cli-pipeline/validated-endpoints.json`, `<cli-repo>/docs/architecture.md`, `<cli-repo>/docs/impl-audit.md`
2. Invoke the `cli-ideate` skill
3. Brainstorm across all 6 categories: daily workflows, resource commands, helpers, recipes, personas, global enhancements
4. Prioritize and tier (P0-P3) with dependency mapping
5. Write `<cli-repo>/docs/feature-backlog.md`

- [ ] **Step 2: Write skill-generator agent**

Write to `cli-generation/agents/skill-generator.md`:

```yaml
---
description: >-
  Skill generation subagent for the cli-generation pipeline. Generates SKILL.md files
  for the built CLI. Must invoke superpowers:skill-creator for full eval harness and
  trigger testing — not just template generation. Reads the CLI repo, feature-backlog.md,
  and architecture.md. Writes skills/ directory.
tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
---
```

Body instructions:
1. Read `<cli-repo>/`, `<cli-repo>/docs/feature-backlog.md`, `<cli-repo>/docs/architecture.md`
2. Read the user's skill selections (passed by orchestrator from Phase 8 pause)
3. **MUST invoke** `superpowers:skill-creator` — NOT just cli-skillgen templates
4. For each selected skill: full creation workflow with trigger descriptions, eval harness, progressive disclosure
5. Write to `<cli-repo>/skills/`

- [ ] **Step 3: Commit**

```bash
cd ~/repos/cli-generation
git add agents/skill-ideator.md agents/skill-generator.md
git commit -m "feat: add skill ideator and skill generator agents"
```

---

### Task 12: Write the /cli-generation Command (Orchestrator)

This is the core of the plugin — the command that chains all 9 agents.

**Files:**
- Create: `cli-generation/commands/cli-generation.md`

- [ ] **Step 1: Write command file**

Write to `cli-generation/commands/cli-generation.md`:

```yaml
---
name: cli-generation
description: >-
  Generate a complete CLI from any API surface. Runs a 10-phase autonomous pipeline:
  input classification, auth recon, API mapping, validation, architecture, audit,
  TDD generation, implementation audit, skill ideation, and skill generation.
  Always pauses at skill ideation for user input.
---
```

Then write the orchestrator body. This is the most critical file — it controls the entire pipeline.

**Phase 0: Input Classification (inline)**
1. Classify the input (URL, spec, proto, SDK, endpoints)
2. Use AskUserQuestion to get:
   - CLI name (3 AI-generated suggestions + user input)
   - Repo path (2 suggestions + user input)
   - Tech stack (TypeScript: Commander.js + Vitest + tsup recommended, Python: Click + pytest + uv, PowerShell: Native + Pester, or user-described custom stack)
3. Create the CLI repo directory at the specified path: `mkdir -p <repo_path>`
4. Initialize git: `cd <repo_path> && git init`
5. Create `.cli-pipeline/` in cwd for pipeline artifacts
6. Write `.cli-pipeline/input-classification.json`
7. Write `.cli-pipeline/pipeline-status.json` with all phases as "pending"

**Phase 1-9: Dispatch Agents Sequentially**

For each phase:
1. Update pipeline-status.json: set current phase to "in_progress"
2. Dispatch the agent via the Agent tool with a prompt that includes:
   - What phase this is
   - Where to read inputs (exact file paths)
   - Where to write outputs (exact file paths)
   - The CLI repo path from input-classification.json
   - For Phase 6: the tech stack choice
   - For Phase 6 (on loop): include audit findings from impl-audit.md
   - For Phase 9: include the user's skill selections from Phase 8
3. Read the agent's result (success/failure summary only — not full output)
4. Update pipeline-status.json: set phase to "completed" with timestamp

**Phase 5 Loop Logic:**
After Phase 5 (architecture audit), read `<cli-repo>/docs/arch-audit.md`. Parse the grade. If grade < B and iteration < 2: dispatch cli-architect agent again with the audit findings, then re-run architecture-auditor. Track iterations in pipeline-status.json.

**Phase 7 Loop Logic:**
Same pattern. After Phase 7 (implementation audit), read `<cli-repo>/docs/impl-audit.md`. If grade < B and iteration < 2: dispatch cli-generator agent with audit findings for targeted fixes, then re-run implementation-auditor.

**Phase 8 Pause:**
After Phase 8 (skill ideation), read `<cli-repo>/docs/feature-backlog.md`. Present the backlog to the user via AskUserQuestion (multiSelect: true). User selects which skills to generate, can add custom ideas. Pass selections to Phase 9.

**Completion:**
After Phase 9, ask user if they want to push to GitHub. If yes, run `scripts/push-to-github.sh`. Report summary: repo URL, audit grades, skill count, endpoint coverage.

**Cross-session resumption:**
At start, check if `.cli-pipeline/pipeline-status.json` exists. If so, offer to resume from the last incomplete phase.

- [ ] **Step 2: Verify command structure**

Confirm: frontmatter parses, all 10 phases are covered, file paths reference correct locations, loop logic is clear, AskUserQuestion usage is correct.

- [ ] **Step 3: Commit**

```bash
cd ~/repos/cli-generation
git add commands/cli-generation.md
git commit -m "feat: add /cli-generation orchestrator command"
```

---

### Task 13: Write push-to-github.sh Script

**Files:**
- Create: `cli-generation/scripts/push-to-github.sh`

- [ ] **Step 1: Write the script**

Write to `cli-generation/scripts/push-to-github.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Usage: push-to-github.sh <cli-repo-path> [repo-name]
# Creates a new private GitHub repo and pushes the CLI

CLI_REPO="${1:?Usage: push-to-github.sh <cli-repo-path> [repo-name]}"
REPO_NAME="${2:-$(basename "$CLI_REPO")}"

cd "$CLI_REPO"

# Ensure we have a git repo with commits
if [ ! -d .git ]; then
  git init
  git add -A
  git commit -m "feat: initial CLI generation"
fi

# Check if remote already exists
if git remote get-url origin &>/dev/null; then
  echo '{"status":"error","message":"Remote origin already exists. Push manually or remove the remote first."}'
  exit 1
fi

# Create GitHub repo (private by default)
gh repo create "$REPO_NAME" --private --source=. --push

# Output result
REPO_URL=$(gh repo view --json url -q '.url')
echo "{\"status\":\"success\",\"repo_url\":\"$REPO_URL\",\"repo_name\":\"$REPO_NAME\"}"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x ~/repos/cli-generation/scripts/push-to-github.sh
```

- [ ] **Step 3: Commit**

```bash
cd ~/repos/cli-generation
git add scripts/push-to-github.sh
git commit -m "feat: add push-to-github script"
```

---

### Task 14: Integration Verification

**Files:**
- No new files. Verify existing structure.

- [ ] **Step 1: Verify plugin structure**

```bash
cd ~/repos/cli-generation
find . -type f | sort
```

Expected output:
```
./.claude-plugin/plugin.json
./agents/api-recon.md
./agents/architecture-auditor.md
./agents/auth-recon.md
./agents/cli-architect.md
./agents/cli-generator.md
./agents/endpoint-validator.md
./agents/implementation-auditor.md
./agents/skill-generator.md
./agents/skill-ideator.md
./commands/cli-generation.md
./README.md
./scripts/push-to-github.sh
./skills/cli-api-recon/SKILL.md
./skills/cli-architect/SKILL.md
./skills/cli-audit/references/quality-checklist.md
./skills/cli-audit/SKILL.md
./skills/cli-ideate/references/category-framework.md
./skills/cli-ideate/SKILL.md
./skills/cli-auth-recon/SKILL.md
./skills/cli-skillgen/references/skill-templates.md
./skills/cli-skillgen/SKILL.md
```

- [ ] **Step 2: Verify all frontmatter parses**

Read each .md file and confirm YAML frontmatter is valid:
- Commands: must have `name` and `description`
- Agents: must have `description`
- Skills: must have `name`, `version`, `description` in frontmatter; SKILL.md file exists in subdirectory

- [ ] **Step 3: Verify cross-references**

Check that:
- Orchestrator command references all 9 agent names correctly
- Agent prompts reference correct skill names
- File paths in agent instructions match the workspace layout (.cli-pipeline/ for intermediates, <cli-repo>/ for CLI output)
- Auth-profile.json schema is consistent between auth-recon agent output and other agents' input expectations

- [ ] **Step 4: Verify spec coverage**

Walk through the spec (docs/specs/2026-04-12-cli-generation-plugin-design.md) section by section:
- [ ] Plugin structure matches spec
- [ ] All 6 skills present
- [ ] All 9 agents present
- [ ] Phase 0 uses AskUserQuestion for name, path, tech stack
- [ ] Auth recon covers 11 auth types
- [ ] OAuth2 uses manual flow (gogcli pattern)
- [ ] No secrets in auth-profile.json
- [ ] API recon parses docs first, reverse-engineers only when needed
- [ ] Tech stack table matches spec (Commander.js, Click, Native PS)
- [ ] Audit loops (Phase 5→4, Phase 7→6) with max 2 iterations
- [ ] Phase 8 always pauses for user skill selection
- [ ] Phase 9 uses skill-creator, not just cli-skillgen
- [ ] Push to GitHub is optional

- [ ] **Step 5: Push to GitHub**

```bash
cd ~/repos/cli-generation
git add -A
git commit -m "chore: integration verification pass"
gh repo create cli-generation --private --source=. --push
```

---

### Task 15: Update cli-toolkit-skills Issue #3

**Files:**
- No files. GitHub API only.

- [ ] **Step 1: Comment on issue with implementation status**

```bash
gh issue comment 3 --repo KalebCole/cli-toolkit-skills --body "Implementation complete. Plugin repo: https://github.com/KalebCole/cli-generation

Components built:
- 1 command: /cli-generation (orchestrator)
- 6 skills: cli-auth-recon, cli-api-recon, cli-architect, cli-audit, cli-ideate, cli-skillgen
- 9 agents: auth-recon, api-recon, endpoint-validator, cli-architect, architecture-auditor, cli-generator, implementation-auditor, skill-ideator, skill-generator
- 1 script: push-to-github.sh

Install: /install github:KalebCole/cli-generation"
```

- [ ] **Step 2: Close issue**

```bash
gh issue close 3 --repo KalebCole/cli-toolkit-skills --reason completed
```

- [ ] **Step 3: Close subsumed issues**

```bash
gh issue close 4 --repo KalebCole/cli-toolkit-skills --reason completed --comment "Subsumed by cli-generation plugin Phase 0 (input classification)"
gh issue close 1 --repo KalebCole/cli-toolkit-skills --reason completed --comment "Subsumed by cli-generation plugin Phase 1 (auth recon with CDP as one strategy)"
gh issue close 2 --repo KalebCole/cli-toolkit-skills --reason completed --comment "Resolved — cli-api-recon is now a real skill in the cli-generation plugin"
```
