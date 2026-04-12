# cli-generation: Autonomous CLI Generation Plugin

**Date:** 2026-04-12
**Author:** Kaleb Cole
**Status:** Draft
**GitHub Issue:** [KalebCole/cli-toolkit-skills#3](https://github.com/KalebCole/cli-toolkit-skills/issues/3)

## Summary

A Claude Code plugin that takes any API surface description -- web URL, OpenAPI spec, SDK reference, GraphQL schema, gRPC proto, raw endpoint list -- and autonomously generates a complete, tested, audited CLI with skills. Each pipeline phase runs in its own subagent. No approval gates. No context bloat.

The plugin supersedes the existing `cli-factory` skill approach.

## Problem

`cli-factory` today:
1. Has hard-coded stop gates between every phase -- breaks flow
2. Accumulates all phase outputs in the orchestrator's context window -- bloats context
3. Only accepts web URLs as input -- excludes specs, SDKs, protos
4. Doesn't generate the actual CLI -- stops at architecture/audit/ideation
5. Lives as a SKILL.md file -- no structured command, agent, or hook support

## What Users See When They Install This Plugin

When someone installs `cli-generation` as a Claude Code plugin:

### Commands (user-invocable)
| Command | Purpose |
|---|---|
| `/cli-generation` | The main orchestrator. Takes an API surface, runs the full pipeline. |

### Skills (auto-activate based on task context)
Each skill is independently useful outside the pipeline. Users can invoke them directly or the agent activates them when relevant.

| Skill | Trigger description | Use outside pipeline? |
|---|---|---|
| `cli-auth-recon` | Discover authentication mechanism for an API | Yes -- any auth discovery task |
| `cli-api-recon` | Map an API surface (endpoints, schemas, rate limits) | Yes -- any API exploration |
| `cli-architect` | Design a CLI from an API spec | Yes -- standalone CLI design |
| `cli-audit` | Grade a CLI against 14-point quality checklist | Yes -- audit any existing CLI |
| `cli-ideate` | Brainstorm features for a CLI across 6 categories | Yes -- ideation for any CLI |
| `cli-skillgen` | Generate SKILL.md files for a CLI | Yes -- skill generation for any CLI |

### Agents (internal -- dispatched by orchestrator only)
Users don't invoke these directly. They're the subagent definitions for each pipeline phase.

| Agent | Phase |
|---|---|
| auth-recon | 1 |
| api-recon | 2 |
| endpoint-validator | 3 |
| cli-architect | 4 |
| architecture-auditor | 5 |
| cli-generator | 6 |
| implementation-auditor | 7 |
| skill-ideator | 8 |
| skill-generator | 9 |

## Architecture

### Plugin Structure

```
cli-generation/
+-- .claude-plugin/
|   +-- plugin.json
+-- commands/
|   +-- cli-generation.md          # /cli-generation command (orchestrator)
+-- agents/
|   +-- auth-recon.md              # Phase 1: Auth discovery
|   +-- api-recon.md               # Phase 2: API surface mapping
|   +-- endpoint-validator.md      # Phase 3: Endpoint validation
|   +-- cli-architect.md           # Phase 4: CLI architecture design
|   +-- architecture-auditor.md    # Phase 5: Architecture audit
|   +-- cli-generator.md           # Phase 6: TDD CLI generation
|   +-- implementation-auditor.md  # Phase 7: Implementation audit
|   +-- skill-ideator.md           # Phase 8: Skill brainstorming
|   +-- skill-generator.md         # Phase 9: Skill generation
+-- skills/
|   +-- cli-auth-recon/
|   |   +-- SKILL.md               # Standalone auth recon skill (reusable)
|   +-- cli-api-recon/
|   |   +-- SKILL.md               # Standalone API recon skill (reusable)
|   +-- cli-architect/
|   |   +-- SKILL.md               # Existing methodology (ported)
|   |   +-- references/
|   +-- cli-audit/
|   |   +-- SKILL.md               # Existing methodology (ported)
|   |   +-- references/
|   |       +-- quality-checklist.md
|   +-- cli-ideate/
|   |   +-- SKILL.md               # Existing methodology (ported)
|   |   +-- references/
|   |       +-- category-framework.md
|   +-- cli-skillgen/
|       +-- SKILL.md               # Existing methodology (ported)
|       +-- references/
|           +-- skill-templates.md
+-- scripts/
    +-- push-to-github.sh          # Creates repo + pushes generated CLI
```

### Pipeline Phases

```
Input (URL | spec | SDK | endpoint list | proto | GraphQL)
  |
  v
Phase 0: INPUT CLASSIFICATION         (orchestrator -- inline)
  |       Ask user: where to create the CLI repo?
  v
Phase 1: AUTH RECON                    (agent: auth-recon)
  |       Try autonomous first (Edge profile, env vars, spec parsing)
  |       Fallback: single targeted prompt if blocked
  |       Output: .cli-pipeline/auth-profile.json (mechanism only, NO secrets)
  v
Phase 2: API RECON                     (agent: api-recon)
  |       Uses auth mechanism from Phase 1
  |       Parse docs/specs first, discover undocumented endpoints if needed
  |       Output: .cli-pipeline/endpoints.json
  v
Phase 3: VALIDATE                      (agent: endpoint-validator)
  |       Hit endpoints with auth, confirm responses
  |       Flag dead/broken/auth-gated
  |       Output: .cli-pipeline/validated-endpoints.json
  v
Phase 4: ARCHITECT                     (agent: cli-architect)
  |       Design CLI: command tree, flags, JSON output, auth commands
  |       Output: <cli-repo>/docs/architecture.md
  v
Phase 5: AUDIT ARCHITECTURE            (agent: architecture-auditor)
  |       14-point quality checklist against design
  |       Output: <cli-repo>/docs/arch-audit.md
  |       If grade < B: loop back to Phase 4 (max 2 iterations)
  v
Phase 6: GENERATE CLI                  (agent: cli-generator)
  |       Uses superpowers:test-driven-development
  |       Write tests first, implement, verify
  |       Output: <cli-repo>/src/, <cli-repo>/tests/
  v
Phase 7: AUDIT IMPLEMENTATION          (agent: implementation-auditor)
  |       14-point quality checklist against code
  |       Output: <cli-repo>/docs/impl-audit.md
  |       If grade < B: loop back to Phase 6 with targeted fixes (max 2 iterations)
  v
Phase 8: IDEATE SKILLS                 (agent: skill-ideator)
  |       6-category brainstorm
  |       Output: <cli-repo>/docs/feature-backlog.md
  |       ALWAYS pauses here for user to select/add/prioritize skills
  v
Phase 9: GENERATE SKILLS               (agent: skill-generator)
  |       Uses superpowers:skill-creator
  |       Full eval harness + trigger testing
  |       Output: <cli-repo>/skills/
  v
DONE -> push to GitHub as new repo
```

### Invocation

```
/cli-generation https://api.example.com
/cli-generation ./openapi-spec.yaml
/cli-generation "Azure SDK for Node.js"
```

The pipeline always pauses at Phase 8 (skill ideation) for the user to review and select skills. No flags needed -- it's just how it works.

## Two Workspaces: Pipeline vs CLI Repo

### Pipeline workspace (`.cli-pipeline/`)
Ephemeral artifacts created during the pipeline run. Lives in the current working directory. Contains only intermediate JSON files and pipeline status. Can be deleted after the CLI is pushed to GitHub.

```
.cli-pipeline/
+-- input-classification.json
+-- auth-profile.json           (mechanism only -- NO secrets)
+-- endpoints.json
+-- validated-endpoints.json
+-- pipeline-status.json        (tracks which phase is current/complete)
```

### CLI repo (`<user-specified-path>/<cli-name>/`)
The actual generated CLI. Its own git repo from the start. The user specifies where it should live and what to name it during Phase 0 (via AskUserQuestion with AI-generated suggestions). The tech stack (TypeScript, Python, PowerShell) is also chosen in Phase 0. All documents generated during the pipeline go in the CLI repo's `docs/` directory -- they ship with the CLI.

```
<cli-name>/
+-- src/
|   +-- commands/
|   +-- helpers/
|   +-- lib/
+-- tests/
+-- docs/
|   +-- architecture.md
|   +-- arch-audit.md
|   +-- impl-audit.md
|   +-- feature-backlog.md
+-- skills/
+-- README.md
+-- package.json (or pyproject.toml, etc.)
```

## Phase Details

### Phase 0: Input Classification (Orchestrator -- Inline)

The `/cli-generation` command classifies the input, collects user preferences, and normalizes everything before dispatching subagents. This is the only phase that prompts the user (besides the auth fallback and skill ideation pause).

**Step 0.1: Classify Input**

| Input type | Detection | Normalized to |
|---|---|---|
| Web URL | Starts with http(s):// | `{ "type": "web_url", "url": "..." }` |
| OpenAPI/Swagger | .yaml/.yml/.json with openapi/swagger key | `{ "type": "openapi_spec", "path": "..." }` |
| GraphQL schema | .graphql/.gql file or URL with /graphql | `{ "type": "graphql_schema", "path_or_url": "..." }` |
| gRPC proto | .proto file | `{ "type": "grpc_proto", "path": "..." }` |
| SDK reference | Package name or docs URL | `{ "type": "sdk_reference", "identifier": "..." }` |
| Raw endpoint list | Text/markdown listing endpoints | `{ "type": "endpoint_list", "content": "..." }` |

**Step 0.2: CLI Name + Repo Path (via AskUserQuestion)**

The orchestrator derives 3 name suggestions from the API/service name and presents them via AskUserQuestion. The user can pick one or type their own. Example:

```
Question: "What should we name this CLI?"
Options:
  - dining-cli (derived from "dining.microsoft.com")
  - msft-dining (abbreviated)
  - cafe-cli (descriptive)
  - [user types their own]

Question: "Where should we create the CLI repo?"
Options:
  - ~/repos/dining-cli/ (standard repos location)
  - ./dining-cli/ (current directory)
  - [user types their own path]
```

**Step 0.3: Tech Stack (via AskUserQuestion)**

The orchestrator asks which language/framework to generate the CLI in. Each option is a fixed, opinionated stack — one CLI framework, one test runner, one build tool. No ambiguity for the generate agent.

```
Question: "What tech stack should the CLI use?"
Options:
  - TypeScript: Commander.js + Vitest + tsup (Recommended)
  - Python: Click + pytest + uv
  - PowerShell: Native module + Pester
  - [user describes their own stack in natural language]
```

If the user types a custom stack (e.g., "Go with Cobra and testify", "Rust with Clap"), the generate agent interprets the natural language input and scaffolds accordingly.

**Fixed stack definitions:**

| Stack | CLI Framework | Test Runner | Build / Run | Package File |
|---|---|---|---|---|
| TypeScript | Commander.js | Vitest | tsx (dev), tsup (build) | package.json |
| Python | Click | pytest | uv run | pyproject.toml |
| PowerShell | Native PS module | Pester | Import-Module | .psd1 manifest |

The tech stack choice is stored in `input-classification.json` and informs Phase 4 (Architect) and Phase 6 (Generate).

Output: `.cli-pipeline/input-classification.json`
```json
{
  "input_type": "web_url",
  "input_value": "https://dining.microsoft.com",
  "cli_name": "dining-cli",
  "repo_path": "~/repos/dining-cli/",
  "tech_stack": "typescript",
  "classified_at": "2026-04-12T10:00:00Z"
}
```

### Phase 1: Auth Recon (Agent: auth-recon, Skill: cli-auth-recon)

Auth must be solved before API recon. Without valid auth, you map 401s, not endpoints.

**SECURITY: auth-profile.json never stores credentials.** It describes the auth mechanism and how to obtain credentials at runtime:

```json
{
  "auth_type": "bearer_token",
  "credential_source": {
    "type": "env_var",
    "var_name": "EXAMPLE_API_TOKEN",
    "fallback": "keyring:example-api"
  },
  "header": "Authorization",
  "prefix": "Bearer",
  "refresh": {
    "type": "oauth2_refresh",
    "endpoint": "/oauth/token",
    "expires_in": 3600
  },
  "discovery_method": "edge_profile_cookies",
  "notes": "Auth discovered via Edge browser profile. Token available in active session."
}
```

The subagent that needs auth reads this profile and fetches the actual credential from the described source (env var, keyring, browser session) at runtime. No secrets touch disk.

**Resolution order (autonomous first):**
1. Reuse existing Edge browser profile cookies/sessions via CDP
2. Check for API keys in env vars, config files, keyrings
3. Parse `securitySchemes` from OpenAPI specs
4. Check cloud provider configs: `~/.aws/config`, `~/.azure/`, `~/.kube/config`
5. Try unauthenticated access

**Supported auth types:**

| Auth type | Discovery strategy | Automated? |
|---|---|---|
| Bearer token (OAuth2, JWT) | WWW-Authenticate header, OpenAPI securitySchemes | Yes |
| API key (header/query) | OpenAPI securitySchemes, common env var names | Yes |
| Cookie/session | CDP Edge profile extraction | Yes |
| Basic auth | WWW-Authenticate: Basic header | Partially -- user provides credentials |
| OAuth2 (auth code, client creds) | OpenAPI securitySchemes, well-known endpoints. **Manual flow (no browser automation needed):** generate auth URL, user approves in any browser, pastes redirect URL back. Pattern from [gogcli](https://github.com/steipete/gogcli). Tokens stored in OS keyring, auto-refresh. | Yes -- manual flow works headless |
| AWS SigV4 / HMAC signing | AWS SDK config, `Authorization: AWS4-HMAC-SHA256` header pattern, env vars (`AWS_ACCESS_KEY_ID`) | Yes for discovery; signing logic generated in CLI |
| Azure AD / Entra ID | `WWW-Authenticate: Bearer realm=...` with Azure tenant, `AZURE_*` env vars, `az account show` | Yes for discovery; token refresh generated in CLI |
| Mutual TLS (mTLS) | TLS handshake failure, cert paths in `~/.certs/`, `.kube/config` | Yes for detection; user confirms cert path |
| Custom header schemes | OpenAPI securitySchemes, API docs parsing | Docs-dependent |
| SAML 2.0 | Metadata endpoints, redirect patterns | No -- requires user configuration |
| No auth (public) | Successful 200 on probe | Yes |

**Fallback (single targeted prompt):**
If autonomous fails, the agent writes `auth-blocked.json` describing what it needs. The orchestrator surfaces this to the user once. This is the **only** human gate, and only when needed.

**Output:** `.cli-pipeline/auth-profile.json`

### Phase 2: API Recon (Agent: api-recon, Skill: cli-api-recon)

The agent uses the `cli-api-recon` skill, which is standalone and reusable outside the pipeline.

**Strategy depends on what's available:**

| Input has... | Recon strategy |
|---|---|
| Docs (OpenAPI, GraphQL schema, proto, SDK docs) | **Parse first.** Extract endpoints, schemas, params directly from documentation. No reverse engineering needed. |
| Docs + running service | Parse docs, then probe for undocumented endpoints not in the spec. Report discrepancies. |
| Running service only (no docs) | **Reverse engineer.** Crawl, probe, sniff network traffic via CDP to discover endpoints. |
| Raw endpoint list | Validate and enrich -- add schemas, params, response formats from probing. |

The skill is smart about this: if you hand it an OpenAPI spec, it parses the spec. It only reverse-engineers when there's no documentation available or when looking for undocumented capabilities beyond what the docs cover.

**Output:** `.cli-pipeline/endpoints.json`

### Phase 3: Validate (Agent: endpoint-validator)

Hit every discovered endpoint with valid auth. Confirm responses match documented schemas.

**Output:** `.cli-pipeline/validated-endpoints.json`

### Phase 4: Architect (Agent: cli-architect)

Uses the ported `cli-architect` skill methodology. Designs the full CLI.

**Output:** `<cli-repo>/docs/architecture.md`

### Phase 5: Audit Architecture (Agent: architecture-auditor)

14-point quality checklist against the design.

**Loop mechanism:**
- Grades the architecture A-F
- If grade < B: feeds findings back to Phase 4 agent for targeted revisions
- Max 2 iterations. If still < B after 2 loops, proceeds with warnings

**Output:** `<cli-repo>/docs/arch-audit.md`

### Phase 6: Generate CLI (Agent: cli-generator)

The big phase. Actually writes the CLI code.

**Must invoke:** `superpowers:test-driven-development`
**Must invoke:** `superpowers:verification-before-completion`

**Output:** `<cli-repo>/src/`, `<cli-repo>/tests/`

### Phase 7: Audit Implementation (Agent: implementation-auditor)

Same 14-point checklist, now against the actual code.

**Loop mechanism:**
- If grade < B: feeds audit findings to Phase 6 agent for targeted fixes
- Additive/corrective, not a regeneration
- Max 2 iterations

**Output:** `<cli-repo>/docs/impl-audit.md`

### Phase 8: Ideate Skills (Agent: skill-ideator)

Uses the ported `cli-ideate` methodology. Brainstorms across 6 categories:
1. Daily workflows
2. New resource commands
3. Helper commands (+ prefix)
4. Recipe skills
5. Persona skills
6. Global enhancements

**Always pauses here.** The orchestrator presents the backlog and the user:
- Selects which skills to generate
- Adds custom skill ideas
- Reprioritizes
- Can skip skill generation entirely

**Output:** `<cli-repo>/docs/feature-backlog.md`

### Phase 9: Generate Skills (Agent: skill-generator)

**Must invoke:** `superpowers:skill-creator` (not just cli-skillgen templates)

**Output:** `<cli-repo>/skills/`

### Completion: Push to GitHub

After all phases complete:
1. The CLI repo is already initialized at the user-specified path
2. Create initial commit with all generated files
3. Derive repo name from CLI name in architecture.md (e.g., `dining-cli` -> `dining-cli` repo)
4. Create new GitHub repo (private by default, user's active `gh` account)
5. Push to remote
6. Report summary to user with repo URL, audit grades, skill count, and endpoint coverage
7. Optionally clean up `.cli-pipeline/` workspace

The user can override the repo name or skip the push entirely.

## Context Management

### Why subagents prevent context bloat

Each subagent starts fresh with only the artifacts it needs. The orchestrator never loads full phase outputs into its own context -- it just tracks phase status.

### What each subagent receives

| Phase | Reads | Writes |
|---|---|---|
| 1 (auth) | input-classification.json | auth-profile.json |
| 2 (recon) | input-classification.json, auth-profile.json | endpoints.json |
| 3 (validate) | auth-profile.json, endpoints.json | validated-endpoints.json |
| 4 (architect) | validated-endpoints.json, auth-profile.json | <cli-repo>/docs/architecture.md |
| 5 (audit arch) | <cli-repo>/docs/architecture.md, quality-checklist.md | <cli-repo>/docs/arch-audit.md |
| 6 (generate) | <cli-repo>/docs/architecture.md, validated-endpoints.json | <cli-repo>/src/, tests/ |
| 7 (audit impl) | <cli-repo>/, quality-checklist.md | <cli-repo>/docs/impl-audit.md |
| 8 (ideate) | validated-endpoints.json, <cli-repo>/docs/architecture.md, impl-audit.md | <cli-repo>/docs/feature-backlog.md |
| 9 (skillgen) | <cli-repo>/, feature-backlog.md, architecture.md | <cli-repo>/skills/ |

## Porting Plan

The existing cli-toolkit-skills repo has 5 SKILL.md files that need to be ported into the plugin:

| Source (cli-toolkit-skills) | Target (plugin) | Changes |
|---|---|---|
| skills/cli-architect/SKILL.md | skills/cli-architect/SKILL.md | Port as-is, update paths |
| skills/cli-audit/SKILL.md + refs | skills/cli-audit/SKILL.md + refs | Port as-is |
| skills/cli-factory/SKILL.md | commands/cli-generation.md | Rewrite as orchestrator command |
| skills/cli-ideate/SKILL.md + refs | skills/cli-ideate/SKILL.md + refs | Port as-is |
| skills/cli-skillgen/SKILL.md + refs | skills/cli-skillgen/SKILL.md + refs | Port as-is |

New components to build:
- `cli-auth-recon` skill (standalone, reusable)
- `cli-api-recon` skill (standalone, reusable)
- 9 agent definitions (one per pipeline phase)
- `/cli-generation` command (orchestrator)
- push-to-github script

## Relationship to Existing Issues

| Issue | Status after this ships |
|---|---|
| #3 (this issue) | Resolved |
| #4 (non-web API support) | Subsumed -- Phase 0 input classification |
| #1 (CDP auth flow) | Subsumed -- one strategy in Phase 1 |
| #2 (api-recon missing from listing) | Resolved -- cli-api-recon is now a real skill |
| #5 (cli-ify / MCP-to-CLI) | Independent -- not affected |

## Open Questions

None. Ready for implementation planning.
