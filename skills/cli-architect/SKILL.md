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

# CLI Architect

Deterministic, JSON-first, agent-friendly CLIs — modeled after the [Google Workspace CLI](https://github.com/googleworkspace/cli).

**This is a methodology, not a persona.** Any agent loads this skill and follows the 3-phase workflow when the task is "build a CLI."

---

## Core Philosophy

**The CLI is the deterministic layer. The agent is the creative layer. Never mix them.**

A well-built CLI:
- Outputs **structured JSON** for every response (success, error, metadata)
- Uses **structured exit codes** so scripts branch on failure type without parsing output
- Provides **helper commands** (`+` prefixed) for common multi-step workflows
- Ships **SKILL.md files** so AI agents know exactly how to use it
- Is **fully usable by humans** — `--help` on every command, `--dry-run` for destructive ops
- Supports **`--format`** flag (json default, table, yaml, csv)
- Does **one thing per command** — composable, pipeable, predictable

---

## The 3-Phase Workflow

Execute phases IN ORDER. Do not skip. Do not combine. Present each phase's output and **STOP** for user confirmation before proceeding.

---

### PHASE 1: TRIAGE

**Goal:** Understand what we're wrapping and map the landscape.

#### Step 1.1 — Identify the Target
Ask/determine:
- **What API/service/tool** are we wrapping? (URL, docs link, repo)
- **What's the goal?** (full API coverage? specific workflows? automation wrapper?)
- **Who uses it?** (humans only? agents only? both?)

#### Step 1.2 — Discover the API Surface
Research the target exhaustively:
- Fetch API docs, OpenAPI/Swagger specs, or Discovery documents
- List all endpoints/resources/methods
- Identify auth mechanisms (OAuth, API key, token, service account, Azure AD)
- Note rate limits, pagination patterns, upload/download support
- Identify which operations are read-only vs write/delete (destructive)

#### Step 1.3 — Assess Constraints
Determine environment constraints:
- **Tech stack:** What language? Default to PowerShell on Windows. Node.js for cross-platform. Python for data-heavy.
- **Dependencies:** Can we use external packages? Any managed-device restrictions?
- **Auth:** Can we reuse existing auth (az CLI, gcloud, env vars)?
- **Network:** Air-gapped? Proxy? Internal-only APIs?

#### Step 1.4 — Triage Output
Present a structured summary:

```
## Triage Summary

**Target:** [service name] ([API docs URL])
**Goal:** [what we're building]
**API Surface:** [N resources, M methods, K helper candidates]
**Auth:** [mechanism]
**Tech Stack:** [language + key deps]
**Constraints:** [any limitations]

### Resources Discovered
| Resource | Methods | Notes |
|----------|---------|-------|
| files | list, get, create, update, delete | CRUD + upload support |
| ...  | ... | ... |

### Candidate Helper Commands
| Helper | What it does | Why it's useful |
|--------|-------------|-----------------|
| +upload | Upload with auto-metadata | Common 3-step flow → 1 command |
| ... | ... | ... |
```

**🛑 STOP.** Present triage summary. Get user confirmation before Phase 2.

---

### PHASE 2: ARCHITECT

**Goal:** Design the complete CLI architecture.

#### Step 2.1 — Command Surface Design

Follow the GWS pattern: `<cli-name> <resource> <method> [flags]`

For simple CLIs (single service): `<cli-name> <resource> <method> [flags]`

Design the command tree:
```
<cli-name>
├── auth
│   ├── login
│   ├── logout
│   └── status
├── <resource-1>
│   ├── list          # GET collection
│   ├── get           # GET single
│   ├── create        # POST
│   ├── update        # PATCH/PUT
│   ├── delete        # DELETE
│   └── +<helper>     # Common workflow shortcut
├── <resource-2>
│   └── ...
├── schema <method>   # Introspect request/response schema
└── version           # Show CLI version
```

#### Step 2.2 — Standard Flags

Every CLI gets these flags:

| Flag | Description | Default |
|------|-------------|---------|
| `--format <FORMAT>` | Output format: json, table, yaml, csv | `json` |
| `--dry-run` | Show the request without executing | off |
| `--verbose` | Show request/response details on stderr | off |
| `--output <PATH>` | Write output to file | stdout |
| `--no-color` | Disable colored output | off |
| `--yes` | Skip confirmation prompts (for CI/CD) | off |
| `--force` | Skip confirmation AND overwrite protection | off |

**`--yes` vs `--force`:**
- `--yes` — suppresses "Are you sure?" prompts. Safe for automation that knows what it's doing.
- `--force` — suppresses confirmation AND allows overwriting existing resources. Use sparingly.
- Neither flag skips `--dry-run` — if both `--dry-run` and `--yes` are set, dry-run wins.

#### Step 2.3 — Exit Codes

Every CLI uses structured exit codes:

| Code | Meaning | When |
|------|---------|------|
| `0` | Success | Command completed normally |
| `1` | API Error | Remote service returned 4xx/5xx |
| `2` | Auth Error | Credentials missing, expired, or invalid |
| `3` | Validation Error | Bad arguments, unknown command, invalid input |
| `4` | Not Found | Requested resource doesn't exist |
| `5` | Internal Error | Unexpected failure in the CLI itself |

#### Step 2.4 — JSON Output Contract

**Every response** is a JSON object. No exceptions. No bare strings. No unstructured text to stdout.

Success:
```json
{
  "status": "success",
  "data": { ... },
  "metadata": {
    "count": 10,
    "nextPageToken": "abc123"
  }
}
```

Error:
```json
{
  "status": "error",
  "error": {
    "code": 1,
    "type": "api_error",
    "message": "Service returned 403: Forbidden",
    "details": { ... }
  }
}
```

**Informational messages go to stderr.** Only JSON goes to stdout.

#### Step 2.5 — Helper Commands

Helpers are `+` prefixed commands that combine multiple API calls into one ergonomic operation.

Criteria for a helper:
- The workflow requires **2+ API calls** that are always done together
- There's a **common use case** that 80%+ of users will hit
- The raw API call requires **boilerplate** the helper can abstract

Design helpers with:
- Minimal required flags (derive what you can)
- Sensible defaults
- `--dry-run` support
- Clear `--help` text

#### Step 2.6 — Auth Design

Follow credential precedence (highest to lowest):

| Priority | Source | Env Var |
|----------|--------|---------|
| 1 | Access token | `<CLI>_TOKEN` |
| 2 | Credentials file | `<CLI>_CREDENTIALS_FILE` |
| 3 | Interactive login | `<cli> auth login` |
| 4 | System credential | OS keyring / existing auth (az, gcloud) |

Support `.env` files for all env vars.

#### Step 2.7 — HTTP Module Design

Every CLI that wraps an HTTP API needs a shared HTTP module. This is where real CLIs break — get it right.

**Retry strategy:**
- Exponential backoff with jitter on `429` and `5xx` responses
- Respect `Retry-After` headers (both delta-seconds and HTTP-date formats)
- Max retries: 3 (configurable via `<CLI>_MAX_RETRIES`)
- Base delay: 1s, max delay: 30s
- Never retry `4xx` errors other than `429` (they won't succeed on retry)

**Pagination:**
- Auto-paginate by default when a `nextPageToken` (or equivalent) is present
- Expose `--page-size <N>` for manual control
- `--page-all` streams results as NDJSON (one JSON object per line)
- `--page-limit <N>` caps total pages (default: 10)
- `--page-delay <MS>` adds delay between pages (default: 100ms, for rate limit safety)

**Timeouts:**
- Default request timeout: 30s (configurable via `<CLI>_TIMEOUT`)
- Default connect timeout: 10s
- Upload/download operations: 5 min timeout

**Rate limiting:**
- Track remaining quota from response headers (`X-RateLimit-Remaining`, `X-RateLimit-Reset`)
- When approaching limit, proactively throttle requests
- Log rate limit status to stderr when `--verbose` is set

**Request/response logging:**
- `--verbose` prints method, URL, headers (redacted), status code, timing to stderr
- `--dry-run` prints the full request that would be sent, then exits with code 0
- Never log request/response bodies unless explicitly requested

#### Step 2.8 — Skill Architecture

Design the SKILL.md file tree:

```
skills/
├── <cli>-shared/SKILL.md          # Auth, global flags, security rules
├── <cli>-<resource>/SKILL.md      # Per-resource API reference
├── <cli>-<helper>/SKILL.md        # Per-helper focused guide
├── recipe-<workflow>/SKILL.md     # Multi-step workflow recipes
└── persona-<role>/SKILL.md        # Role-based skill bundles
```

Each SKILL.md follows this frontmatter:
```yaml
---
name: <skill-name>
version: 1.0.0
description: "<one-line description>"
metadata:
  category: "productivity|recipe|persona"
  requires:
    bins: ["<cli-name>"]
    skills: ["<dependent-skills>"]  # for recipes/personas
    cliHelp: "<cli-name> <resource> --help"
---
```

#### Step 2.9 — Architecture Output

Present the full architecture document:
- Command tree (visual)
- Flags table
- Exit codes
- JSON output contract
- Helper commands with signatures
- Auth flow
- HTTP module behavior
- Skill tree
- Security rules

**🛑 STOP.** Present architecture. Get user confirmation before Phase 3.

---

### PHASE 3: BUILD

**Goal:** Generate the project scaffold with working code.

#### Step 3.1 — Project Structure

```
<cli-name>/
├── README.md                    # GWS-style README
├── package.json                 # or pyproject.toml, Cargo.toml
├── .env.example                 # All env vars with descriptions
├── src/                         # or scripts/
│   ├── cli.{ts,py,ps1}         # Main entry point
│   ├── commands/                # One file per resource
│   │   ├── auth.{ts,py,ps1}
│   │   └── <resource>.{ts,py,ps1}
│   ├── helpers/                 # + commands
│   │   └── <helper>.{ts,py,ps1}
│   └── lib/                     # Shared utilities
│       ├── http.{ts,py,ps1}    # HTTP client (see §2.7)
│       ├── output.{ts,py,ps1}  # JSON/table/yaml/csv formatters
│       ├── auth.{ts,py,ps1}    # Credential chain
│       └── errors.{ts,py,ps1}  # Structured error types
├── skills/                      # Agent skills
│   ├── <cli>-shared/SKILL.md
│   ├── <cli>-<resource>/SKILL.md
│   └── recipe-<workflow>/SKILL.md
├── tests/
└── .github/workflows/ci.yml
```

#### Step 3.2 — Core Implementation

**Language priority:** Default to PowerShell on Windows/Corp devices. Use Node.js for cross-platform CLIs. Use Python for data-heavy/scripting CLIs. When the user doesn't specify, ask in Phase 1.

All three skeletons below are production-ready starting points — not pseudocode.

##### PowerShell Skeleton

```powershell
[CmdletBinding()]
param(
    [Parameter(Position=0)] [string]$Resource,
    [Parameter(Position=1)] [string]$Method,
    [string]$Format = "json",
    [switch]$DryRun,
    [switch]$Yes,
    [switch]$Force,
    [switch]$Verbose,
    [string]$Output
)

# JSON output helper
function Write-JsonOutput {
    param([hashtable]$Data, [int]$ExitCode = 0)
    $statusText = $(if ($ExitCode -eq 0) { "success" } else { "error" })
    $result = @{ status = $statusText; data = $Data }
    $json = $result | ConvertTo-Json -Depth 10 -Compress
    if ($Output) { $json | Set-Content $Output } else { Write-Output $json }
    exit $ExitCode
}

# Error handler
function Write-JsonError {
    param([string]$Message, [int]$Code = 5, [string]$Type = "internal_error")
    $err = @{ status = "error"; error = @{ code = $Code; type = $Type; message = $Message } }
    $err | ConvertTo-Json -Depth 5 -Compress | Write-Output
    exit $Code
}

# Confirmation gate for destructive operations
function Confirm-Destructive {
    param([string]$Action)
    if ($DryRun) { Write-Host "[dry-run] Would $Action" -ForegroundColor Yellow; exit 0 }
    if (-not $Yes -and -not $Force) {
        $answer = Read-Host "Confirm: $Action? (y/N)"
        if ($answer -notin @('y','yes')) { Write-JsonError "Aborted by user" -Code 3 -Type "validation_error" }
    }
}

# HTTP client with retry
function Invoke-ApiRequest {
    param(
        [string]$Uri,
        [string]$Method = "GET",
        [hashtable]$Headers = @{},
        [object]$Body,
        [int]$MaxRetries = 3
    )
    $attempt = 0
    while ($attempt -le $MaxRetries) {
        try {
            $params = @{ Uri = $Uri; Method = $Method; Headers = $Headers; UseBasicParsing = $true }
            if ($Body) { $params.Body = ($Body | ConvertTo-Json -Depth 10); $params.ContentType = "application/json" }
            if ($Verbose) { Write-Host "$Method $Uri (attempt $($attempt + 1))" -ForegroundColor DarkGray }
            $response = Invoke-WebRequest @params
            return ($response.Content | ConvertFrom-Json)
        } catch {
            $status = $_.Exception.Response.StatusCode.Value__
            if ($status -eq 429 -or $status -ge 500) {
                $attempt++
                if ($attempt -gt $MaxRetries) { Write-JsonError $_.Exception.Message -Code 1 -Type "api_error" }
                $retryAfter = $_.Exception.Response.Headers["Retry-After"]
                $delay = if ($retryAfter) { [int]$retryAfter } else { [math]::Min(30, [math]::Pow(2, $attempt) + (Get-Random -Maximum 1000) / 1000) }
                Write-Host "Retrying in ${delay}s (attempt $attempt/$MaxRetries)..." -ForegroundColor DarkGray
                Start-Sleep -Seconds $delay
            } elseif ($status -eq 401 -or $status -eq 403) {
                Write-JsonError $_.Exception.Message -Code 2 -Type "auth_error"
            } elseif ($status -eq 404) {
                Write-JsonError $_.Exception.Message -Code 4 -Type "not_found"
            } else {
                Write-JsonError $_.Exception.Message -Code 1 -Type "api_error"
            }
        }
    }
}

# Route to command handler
switch ($Resource) {
    "auth"    { & "$PSScriptRoot\commands\auth.ps1" @PSBoundParameters }
    "version" { Write-JsonOutput @{ version = "0.1.0"; cli = "<cli-name>" } }
    default   { Write-JsonError "Unknown resource: $Resource" -Code 3 -Type "validation_error" }
}
```

##### Node.js Skeleton

```javascript
#!/usr/bin/env node
import { Command } from 'commander';

// --- Output helpers ---
function jsonOutput(data, metadata = {}) {
  console.log(JSON.stringify({ status: 'success', data, metadata }));
}

function jsonError(message, code = 5, type = 'internal_error') {
  console.log(JSON.stringify({ status: 'error', error: { code, type, message } }));
  process.exit(code);
}

// --- Confirmation gate ---
async function confirmDestructive(action, opts) {
  if (opts.dryRun) { console.error(`[dry-run] Would ${action}`); process.exit(0); }
  if (!opts.yes && !opts.force) {
    const readline = await import('readline');
    const rl = readline.createInterface({ input: process.stdin, output: process.stderr });
    const answer = await new Promise(r => rl.question(`Confirm: ${action}? (y/N) `, r));
    rl.close();
    if (!['y', 'yes'].includes(answer.toLowerCase())) jsonError('Aborted by user', 3, 'validation_error');
  }
}

// --- HTTP client with retry ---
async function apiRequest(url, { method = 'GET', headers = {}, body, maxRetries = 3, verbose = false } = {}) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      if (verbose) console.error(`${method} ${url} (attempt ${attempt + 1})`);
      const opts = { method, headers: { 'Content-Type': 'application/json', ...headers } };
      if (body) opts.body = JSON.stringify(body);
      const res = await fetch(url, opts);
      if (!res.ok) {
        const status = res.status;
        if ((status === 429 || status >= 500) && attempt < maxRetries) {
          const retryAfter = res.headers.get('Retry-After');
          const delay = retryAfter ? parseInt(retryAfter) * 1000 : Math.min(30000, 2 ** attempt * 1000 + Math.random() * 1000);
          console.error(`Retrying in ${Math.round(delay / 1000)}s (attempt ${attempt + 1}/${maxRetries})...`);
          await new Promise(r => setTimeout(r, delay));
          continue;
        }
        if (status === 401 || status === 403) jsonError(await res.text(), 2, 'auth_error');
        if (status === 404) jsonError(await res.text(), 4, 'not_found');
        jsonError(await res.text(), 1, 'api_error');
      }
      return await res.json();
    } catch (err) {
      if (attempt >= maxRetries) jsonError(err.message, 5, 'internal_error');
    }
  }
}

// --- CLI definition ---
const program = new Command();
program
  .name('<cli-name>')
  .description('<one-line description>')
  .version('0.1.0')
  .option('--format <format>', 'Output format', 'json')
  .option('--dry-run', 'Preview without executing')
  .option('--yes', 'Skip confirmation prompts')
  .option('--force', 'Skip confirmation and overwrite protection')
  .option('--verbose', 'Show request details on stderr')
  .option('--output <path>', 'Write output to file');

program.command('version').action(() => jsonOutput({ version: '0.1.0', cli: '<cli-name>' }));
// program.command('<resource>').addCommand(...)

program.parse();
```

##### Python Skeleton

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["click", "httpx"]
# ///
"""<cli-name>: <one-line description>."""
import json, sys, time, random
import click
import httpx

# --- Output helpers ---
def json_output(data: dict, **metadata) -> None:
    click.echo(json.dumps({"status": "success", "data": data, "metadata": metadata}))

def json_error(message: str, code: int = 5, error_type: str = "internal_error") -> None:
    click.echo(json.dumps({"status": "error", "error": {"code": code, "type": error_type, "message": message}}))
    sys.exit(code)

# --- Confirmation gate ---
def confirm_destructive(action: str, dry_run: bool, yes: bool, force: bool) -> None:
    if dry_run:
        click.echo(f"[dry-run] Would {action}", err=True)
        sys.exit(0)
    if not yes and not force:
        if not click.confirm(f"Confirm: {action}?", default=False, err=True):
            json_error("Aborted by user", code=3, error_type="validation_error")

# --- HTTP client with retry ---
def api_request(
    url: str, method: str = "GET", headers: dict = None, body: dict = None,
    max_retries: int = 3, timeout: float = 30.0, verbose: bool = False,
) -> dict:
    headers = headers or {}
    client = httpx.Client(timeout=timeout)
    for attempt in range(max_retries + 1):
        try:
            if verbose:
                click.echo(f"{method} {url} (attempt {attempt + 1})", err=True)
            response = client.request(method, url, headers=headers, json=body)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if (status == 429 or status >= 500) and attempt < max_retries:
                retry_after = e.response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else min(30, 2**attempt + random.random())
                click.echo(f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})...", err=True)
                time.sleep(delay)
                continue
            if status in (401, 403):
                json_error(str(e), code=2, error_type="auth_error")
            if status == 404:
                json_error(str(e), code=4, error_type="not_found")
            json_error(str(e), code=1, error_type="api_error")
        except httpx.RequestError as e:
            if attempt >= max_retries:
                json_error(str(e), code=5, error_type="internal_error")
    json_error("Max retries exceeded", code=1, error_type="api_error")

# --- CLI definition ---
@click.group()
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "table", "yaml", "csv"]))
@click.option("--dry-run", is_flag=True, help="Preview without executing")
@click.option("--yes", is_flag=True, help="Skip confirmation prompts")
@click.option("--force", is_flag=True, help="Skip confirmation and overwrite protection")
@click.option("--verbose", is_flag=True, help="Show request details on stderr")
@click.option("--output", type=click.Path(), help="Write output to file")
@click.pass_context
def cli(ctx, fmt, dry_run, yes, force, verbose, output):
    ctx.ensure_object(dict)
    ctx.obj.update(format=fmt, dry_run=dry_run, yes=yes, force=force, verbose=verbose, output=output)

@cli.command()
def version():
    json_output({"version": "0.1.0", "cli": "<cli-name>"})

if __name__ == "__main__":
    cli()
```

#### Step 3.3 — SKILL.md Generation

Generate skills following the GWS layered pattern:

**Shared skill** (auth + global flags):
```markdown
---
name: <cli>-shared
version: 1.0.0
description: "<cli> CLI: Shared patterns for authentication, global flags, and output formatting."
metadata:
  requires:
    bins: ["<cli-name>"]
---

# <cli> — Shared Reference

## Installation
[install instructions]

## Authentication
[auth commands and precedence table]

## Global Flags
[flags table including --yes and --force]

## CLI Syntax
`<cli> <resource> <method> [flags]`

## Security Rules
- Never output secrets
- Confirm before write/delete (unless --yes/--force)
- Prefer --dry-run for destructive operations
- Stderr for humans, stdout for machines
```

**Resource skill** (per-API-resource):
```markdown
---
name: <cli>-<resource>
version: 1.0.0
description: "<Service>: <what this resource does>."
metadata:
  requires:
    bins: ["<cli-name>"]
    cliHelp: "<cli-name> <resource> --help"
---

# <resource>

> **PREREQUISITE:** Read `../<cli>-shared/SKILL.md` for auth, global flags, and security rules.

## Helper Commands
[table of + helpers]

## API Methods
[list of methods with descriptions]

## Examples
[real, working command examples]

## Discovering Commands
`<cli> schema <resource>.<method>` to introspect parameters and types.
```

**Recipe skill** (multi-step workflow):
```markdown
---
name: recipe-<workflow-name>
version: 1.0.0
description: "<What this recipe does, end to end>."
metadata:
  category: "recipe"
  requires:
    bins: ["<cli-name>"]
    skills: ["<cli>-<resource1>", "<cli>-<resource2>"]
---

# <Workflow Name>

> **PREREQUISITE:** Load: `<cli>-<resource1>`, `<cli>-<resource2>`

## Steps
1. [First command with explanation]
2. [Second command]
3. [Third command]
```

#### Step 3.4 — Copilot Skill File

Generate a `.skill` description for Copilot CLI registration:

```yaml
---
name: <cli-name>
description: >-
  <one-line description>. Use when user asks to: <trigger phrases>.
  Triggers: "<trigger1>", "<trigger2>", "<trigger3>".
---
```

#### Step 3.5 — Test Scaffold

Generate test cases for:
- [ ] Each resource's CRUD operations (list, get, create, update, delete)
- [ ] Each helper command (happy path + error cases)
- [ ] Auth flow (login, token refresh, expired credentials, missing credentials)
- [ ] HTTP retry behavior (429 → retry, 500 → retry, 400 → no retry)
- [ ] Pagination (auto-paginate, --page-size, --page-limit)
- [ ] JSON output compliance (every response is valid JSON with status field)
- [ ] Exit code correctness (each error type maps to correct code)
- [ ] `--dry-run` behavior (no side effects, exits 0)
- [ ] `--yes`/`--force` flags (skip confirmation, allow overwrite)
- [ ] `--format` flag (json, table, yaml, csv all produce valid output)
- [ ] Error responses include code, type, and message fields

#### Step 3.6 — README Generation

Generate a GWS-style README with these sections:
1. One-liner description + badges
2. Install instructions
3. Quick Start (3 commands max)
4. "Why `<cli-name>`?" (for humans / for agents)
5. Authentication (precedence table + examples)
6. Command reference (resource → method table)
7. Helper command table with examples
8. Exit codes table
9. Environment variables table
10. Architecture section
11. Troubleshooting
12. Development (build, lint, test commands)

**🛑 STOP.** Present the generated scaffold for review before writing to disk.

---

## Quick Reference Tables

### Command Pattern
```
<cli> <resource> <method> [flags]
<cli> <resource> +<helper> [flags]
<cli> auth login|logout|status
<cli> schema <resource>.<method>
```

### Standard Flags
| Flag | Description | Default |
|------|-------------|---------|
| `--format <F>` | json, table, yaml, csv | json |
| `--dry-run` | Preview without executing | off |
| `--verbose` | Request/response on stderr | off |
| `--output <PATH>` | Write to file | stdout |
| `--no-color` | Disable ANSI colors | off |
| `--yes` | Skip confirmation prompts | off |
| `--force` | Skip confirm + overwrite protection | off |

### Exit Codes
| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | API error (remote 4xx/5xx) |
| 2 | Auth error |
| 3 | Validation error |
| 4 | Not found |
| 5 | Internal error |

### Auth Precedence
| Priority | Source | Env Var |
|----------|--------|---------|
| 1 | Access token | `<CLI>_TOKEN` |
| 2 | Credentials file | `<CLI>_CREDENTIALS_FILE` |
| 3 | Interactive login | `<cli> auth login` |
| 4 | System credential | OS keyring / az / gcloud |

### Skill Taxonomy
| Layer | Directory | Purpose |
|-------|-----------|---------|
| Shared | `<cli>-shared/` | Auth, flags, security |
| Service | `<cli>-<resource>/` | Per-resource API ref |
| Helper | `<cli>-<helper>/` | Per-helper guide |
| Recipe | `recipe-<name>/` | Multi-step workflows |
| Persona | `persona-<role>/` | Role-based bundles |

### Helper Command Criteria
A workflow deserves a `+helper` when:
- Requires **2+ API calls** always done together
- **80%+ of users** will hit this use case
- Raw API call has **boilerplate** the helper eliminates

---

## Quality Checklist (Pre-Delivery Gate)

Before presenting the scaffold:

- [ ] Every command outputs valid JSON to stdout
- [ ] Exit codes match the contract (0-5)
- [ ] `--help` works on every command and subcommand
- [ ] `--dry-run` works on every write/delete command
- [ ] `--yes`/`--force` work on every destructive command
- [ ] `--format json` is default; table/yaml/csv also work
- [ ] Auth follows the credential precedence chain
- [ ] HTTP client retries 429/5xx with exponential backoff + jitter
- [ ] Pagination auto-paginates with NDJSON streaming
- [ ] SKILL.md files exist for: shared, each resource, each helper
- [ ] README follows GWS pattern
- [ ] No secrets in output or logs
- [ ] Errors are JSON objects with code, type, message
- [ ] Tests cover CRUD, auth, retry, pagination, output format, exit codes

---

## Anti-Patterns (Never Do These)

- ❌ Mixing human-readable text with JSON on stdout
- ❌ Using exit code 1 for everything
- ❌ Requiring interactive prompts with no `--yes` escape hatch
- ❌ Hardcoding credentials or tokens
- ❌ Building agent logic into the CLI (CLI = deterministic; agent = separate)
- ❌ Returning different JSON shapes for the same command
- ❌ Skipping `--dry-run` on write commands
- ❌ Monolithic SKILL.md files (use layered skills)
- ❌ Retrying 4xx errors (they won't succeed on retry)
- ❌ Logging request/response bodies by default (privacy risk)
- ❌ Swallowing errors silently (every failure → JSON error + nonzero exit)

---

## Reference Implementation

The canonical reference for all design decisions is:
**[Google Workspace CLI (gws)](https://github.com/googleworkspace/cli)**

When in doubt: check how `gws` handles it.
