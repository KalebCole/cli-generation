# cli-generation

> Generate complete, tested, audited CLIs from any API surface. A [Claude Code](https://docs.anthropic.com/en/docs/claude-code) plugin.

## Try it now

```bash
/cli-generation https://api.example.com
```

## Install

```bash
# 1. Add the marketplace
claude plugin marketplace add https://github.com/KalebCole/cli-generation.git

# 2. Install the plugin
claude plugin install cli-generation
```

Requires the `superpowers` plugin for TDD and skill creation:

```bash
claude plugin install superpowers
```

## What It Does

Point `/cli-generation` at any API surface and it autonomously builds a production-grade CLI:

- **Auth discovery** — figures out how the API authenticates (11 auth types)
- **API mapping** — parses docs or reverse-engineers endpoints
- **Validation** — hits every endpoint, confirms responses
- **Architecture** — designs command tree, flags, JSON output contract
- **Code generation** — writes the CLI using TDD (tests first)
- **Quality audit** — grades against 14-point checklist, loops until grade >= B
- **Skill generation** — creates SKILL.md files so AI agents can use the CLI

Each phase runs in its own subagent. No context bloat.

## Supported Inputs

```bash
# Web URL
/cli-generation https://dining.microsoft.com

# OpenAPI / Swagger spec
/cli-generation ./openapi-spec.yaml

# GraphQL schema
/cli-generation ./schema.graphql

# gRPC proto
/cli-generation ./service.proto

# SDK reference
/cli-generation "Azure SDK for Node.js"

# Raw endpoint list
/cli-generation "GET /users, POST /users, GET /users/:id, DELETE /users/:id"
```

## The Pipeline

```
Input (URL | spec | SDK | endpoint list | proto | GraphQL)
  │
  ▼
Phase 0: CLASSIFY INPUT ──────────── You pick: CLI name, repo path, tech stack
  │
  ▼
Phase 1: AUTH RECON ───────────────── Agent: auth-recon
  │  Try Edge cookies, env vars, OpenAPI, cloud configs, unauthenticated probe
  │  Fallback: asks you once if stuck
  ▼
Phase 2: API RECON ────────────────── Agent: api-recon
  │  Parse docs first. Reverse-engineer only when needed.
  ▼
Phase 3: VALIDATE ─────────────────── Agent: endpoint-validator
  │  Hit endpoints with auth, confirm responses match schemas
  ▼
Phase 4: ARCHITECT ────────────────── Agent: cli-architect
  │  Command tree, flags, JSON output, auth commands, HTTP module
  ▼
Phase 5: AUDIT ARCHITECTURE ───────── Agent: architecture-auditor
  │  14-point quality checklist. Loop → Phase 4 if grade < B (max 2x)
  ▼
Phase 6: GENERATE CLI ─────────────── Agent: cli-generator
  │  TDD: write tests first, implement, verify. Full src/ + tests/
  ▼
Phase 7: AUDIT IMPLEMENTATION ─────── Agent: implementation-auditor
  │  14-point checklist against code. Loop → Phase 6 if grade < B (max 2x)
  ▼
Phase 8: IDEATE SKILLS ────────────── Agent: skill-ideator
  │  6-category brainstorm. PAUSE: you pick which skills to generate.
  ▼
Phase 9: GENERATE SKILLS ──────────── Agent: skill-generator
  │  Full SKILL.md files with eval harness and trigger testing
  ▼
DONE ──────────────────────────────── Optional: push to GitHub
```

## Tech Stack Options

The CLI it generates uses your choice of stack:

| Stack | CLI Framework | Test Runner | Build / Run | Package File |
|-------|--------------|-------------|-------------|-------------|
| **TypeScript** (recommended) | Commander.js | Vitest | tsx / tsup | package.json |
| **Python** | Click | pytest | uv run | pyproject.toml |
| **PowerShell** | Native module | Pester | Import-Module | .psd1 |
| **Custom** | You describe it | You describe it | You describe it | — |

## What You Get

### 1 Command

| Command | What it does |
|---------|-------------|
| `/cli-generation` | The orchestrator. Takes an API surface, runs all 9 phases. |

### 6 Skills (independently useful)

Each skill works standalone — you don't need to run the full pipeline.

| Skill | Use when you want to... |
|-------|------------------------|
| `cli-auth-recon` | Figure out how an API authenticates |
| `cli-api-recon` | Map an API's endpoints, schemas, rate limits |
| `cli-architect` | Design a CLI architecture from scratch |
| `cli-audit` | Grade any CLI against the 14-point quality checklist |
| `cli-ideate` | Brainstorm features for a CLI across 6 categories |
| `cli-skillgen` | Generate SKILL.md files for a CLI |

### 9 Internal Agents

Dispatched by the orchestrator — you don't invoke these directly.

| Agent | Phase | Reads | Writes |
|-------|-------|-------|--------|
| auth-recon | 1 | input-classification.json | auth-profile.json |
| api-recon | 2 | input-classification, auth-profile | endpoints.json |
| endpoint-validator | 3 | auth-profile, endpoints | validated-endpoints.json |
| cli-architect | 4 | validated-endpoints, auth-profile | architecture.md |
| architecture-auditor | 5 | architecture.md | arch-audit.md |
| cli-generator | 6 | architecture.md, validated-endpoints | src/, tests/ |
| implementation-auditor | 7 | CLI repo codebase | impl-audit.md |
| skill-ideator | 8 | validated-endpoints, architecture | feature-backlog.md |
| skill-generator | 9 | CLI repo, feature-backlog | skills/ |

## Auth Discovery

The auth-recon agent tries 5 strategies autonomously before asking you anything:

1. **Edge browser cookies** — CDP extraction from active sessions
2. **Environment variables** — `*_TOKEN`, `*_KEY`, `*_SECRET`
3. **OpenAPI securitySchemes** — parsed from specs
4. **Cloud provider configs** — `~/.aws/`, `~/.azure/`, `~/.kube/`
5. **Unauthenticated probe** — check if the API is public

Supports 11 auth types: Bearer, API key, Cookie, Basic, OAuth2 (manual flow), AWS SigV4, Azure AD, mTLS, Custom headers, SAML, No auth.

**Security:** `auth-profile.json` never stores actual secrets — only mechanism descriptions and credential source references.

## Quality Checklist

The 14-point audit checklist grades CLIs on:

| # | Check | Weight |
|---|-------|--------|
| 1 | JSON output to stdout | 10 |
| 2 | Structured exit codes (0-5) | 5 |
| 3 | --help on every command | 5 |
| 4 | --dry-run on write/delete | 5 |
| 5 | --yes/--force on destructive | 5 |
| 6 | --format flag (json/table/yaml/csv) | 10 |
| 7 | Auth credential precedence chain | 8 |
| 8 | HTTP retry on 429/5xx | 8 |
| 9 | Auto-pagination | 7 |
| 10 | Layered SKILL.md files | 8 |
| 11 | GWS-pattern README | 5 |
| 12 | No secrets in output/logs | 8 |
| 13 | JSON error objects (code, type, message) | 8 |
| 14 | Test coverage (CRUD, auth, retry, pagination) | 8 |

Grade scale: A (90-100%) · B (80-89%) · C (70-79%) · D (60-69%) · F (<60%)

The pipeline loops Phases 4→5 and 6→7 until grade >= B (max 2 iterations).

## Cross-Session Resume

If a pipeline run is interrupted, `/cli-generation` detects the existing `.cli-pipeline/pipeline-status.json` and offers to resume from the last incomplete phase.

## External Dependencies

| Dependency | Used by | Phase |
|------------|---------|-------|
| `superpowers:test-driven-development` | cli-generator | 6 |
| `superpowers:verification-before-completion` | cli-generator | 6 |
| `superpowers:skill-creator` | skill-generator | 9 |

If superpowers isn't installed, these phases use fallback behavior (no TDD cycle, template-based skill generation).

## Design Spec

Full architecture, phase details, and context management strategy:
[docs/specs/2026-04-12-cli-generation-plugin-design.md](docs/specs/2026-04-12-cli-generation-plugin-design.md)

## License

MIT
