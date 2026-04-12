# cli-generation

Autonomous CLI generation from any API surface.

## Installation

```bash
/install github:KalebCole/cli-generation
```

## What You Get

**1 Command:**
- `/cli-generation` — The orchestrator. Takes an API surface, runs the full 9-phase pipeline.

**6 Skills (independently useful):**
- `cli-auth-recon` — Discover authentication mechanisms for any API
- `cli-api-recon` — Map API surfaces (endpoints, schemas, rate limits)
- `cli-architect` — Design CLIs from API specs
- `cli-audit` — Grade CLIs against a 14-point quality checklist
- `cli-ideate` — Brainstorm features for CLIs across 6 categories
- `cli-skillgen` — Generate SKILL.md files for CLIs

**9 Internal Agents (dispatched by the orchestrator):**
auth-recon, api-recon, endpoint-validator, cli-architect, architecture-auditor, cli-generator, implementation-auditor, skill-ideator, skill-generator

## The Pipeline

```
Input (web URL, OpenAPI spec, SDK, endpoint list, proto, GraphQL)
  |
  v
Phase 1: AUTH RECON
  |       Autonomous auth discovery (env vars, Edge profile, spec parsing)
  v
Phase 2: API RECON
  |       Parse docs or reverse-engineer API surface
  v
Phase 3: VALIDATE
  |       Hit endpoints, confirm responses
  v
Phase 4: ARCHITECT
  |       Design the CLI: commands, flags, output formats
  v
Phase 5: AUDIT ARCHITECTURE
  |       14-point quality checklist (loop if grade < B)
  v
Phase 6: GENERATE CLI
  |       Write tests first, implement, verify
  v
Phase 7: AUDIT IMPLEMENTATION
  |       14-point checklist against code (loop if grade < B)
  v
Phase 8: IDEATE SKILLS
  |       Brainstorm features (6-category framework)
  |       PAUSE: user selects/prioritizes skills
  v
Phase 9: GENERATE SKILLS
  |       Full SKILL.md files with eval harness
  v
DONE: Push to GitHub
```

## Usage

```bash
/cli-generation https://api.example.com
/cli-generation ./openapi-spec.yaml
/cli-generation "Azure SDK for Node.js"
```

Each phase runs in its own subagent. No approval gates between phases. No context bloat — each agent sees only what it needs.

The pipeline always pauses at Phase 8 for skill ideation. You review the brainstorm, select which skills to generate, and decide what to build next.

## External Dependencies

The pipeline's Phase 6 (CLI generation) and Phase 9 (skill generation) invoke skills from the `superpowers` plugin:

- `superpowers:test-driven-development` — used by cli-generator agent
- `superpowers:verification-before-completion` — used by cli-generator agent
- `superpowers:skill-creator` — used by skill-generator agent

Install superpowers first: `/install github:claude-plugins-official/superpowers`

If superpowers is not installed, these phases will use fallback behavior (no TDD cycle, template-based skill generation).

## Design Spec

Full architecture, phase details, and context management strategy: [docs/specs/2026-04-12-cli-generation-plugin-design.md](docs/specs/2026-04-12-cli-generation-plugin-design.md)
