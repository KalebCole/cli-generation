---
name: cli-generation
description: >-
  Generate a complete CLI from any API surface. Runs a 10-phase autonomous pipeline:
  input classification, auth recon, API mapping, validation, architecture, audit,
  TDD generation, implementation audit, skill ideation, and skill generation.
  Always pauses at skill ideation for user input.
---

# /cli-generation Orchestrator

You are the orchestrator for the cli-generation pipeline. You chain 9 subagents sequentially, managing state through `.cli-pipeline/` artifacts. You never load full phase outputs into your own context — you track status and dispatch.

---

## Cross-Session Resumption

Before doing anything else:

1. Check if `.cli-pipeline/pipeline-status.json` exists in the current working directory.
2. If it exists, read it and identify the last completed phase and the first incomplete phase.
3. Also read `.cli-pipeline/input-classification.json` to recover `cli_name`, `repo_path`, and `tech_stack`.
4. Present the status to the user:
   ```
   Found an in-progress pipeline for "<cli_name>".
   Completed: Phase 0 (input), Phase 1 (auth), Phase 2 (api-recon)
   Next: Phase 3 (endpoint validation)
   Resume from Phase 3, or start fresh?
   ```
5. If the user chooses to resume, skip to the first incomplete phase.
6. If the user declines, delete the `.cli-pipeline/` directory and start from Phase 0.

---

## Phase 0: Input Classification (Inline)

This phase runs directly in the orchestrator — no subagent needed.

### Step 0.1: Classify Input

Examine the user's input (the argument passed to `/cli-generation`) and classify it:

| Input Pattern | Type |
|---|---|
| Starts with `http://` or `https://` | `web_url` |
| File ending `.yaml`, `.yml`, `.json` containing `openapi` or `swagger` key | `openapi_spec` |
| File ending `.graphql`, `.gql`, or URL containing `/graphql` | `graphql_schema` |
| File ending `.proto` | `grpc_proto` |
| Package name or docs URL (e.g., `@azure/cosmos`, `boto3`) | `sdk_reference` |
| Text listing endpoints (markdown, plain text) | `endpoint_list` |

If classification is ambiguous, use AskUserQuestion to confirm.

### Step 0.2: CLI Name

Use AskUserQuestion to get the CLI name:
- Derive 3 name suggestions from the API/service name (e.g., for `https://dining.microsoft.com`: `dining-cli`, `msft-dining`, `cafe-cli`)
- Present them as options
- Let the user pick one or type their own

### Step 0.3: Repo Path

Use AskUserQuestion to get the repo path:
- Suggest `~/repos/<cli-name>/` and `./<cli-name>/`
- Let the user type their own path

### Step 0.4: Tech Stack

Use AskUserQuestion to get the tech stack:
- **TypeScript:** Commander.js + Vitest + tsup (Recommended)
- **Python:** Click + pytest + uv
- **PowerShell:** Native module + Pester
- **Custom:** User describes their own stack in natural language

### Step 0.5: Create Workspace

1. Create the CLI repo directory:
   ```bash
   mkdir -p <repo_path>
   ```
2. Initialize git in the CLI repo:
   ```bash
   cd <repo_path> && git init
   ```
3. Create the pipeline artifacts directory in cwd:
   ```bash
   mkdir -p .cli-pipeline
   ```

### Step 0.6: Write Input Classification

Write `.cli-pipeline/input-classification.json`:

```json
{
  "input_type": "<web_url|openapi_spec|graphql_schema|grpc_proto|sdk_reference|endpoint_list>",
  "input_value": "<the URL, file path, package name, or raw text>",
  "cli_name": "<chosen-name>",
  "repo_path": "<absolute-path-to-cli-repo>",
  "tech_stack": "<typescript|python|powershell|custom>",
  "tech_stack_details": "<if custom, the user's description — otherwise omit>",
  "classified_at": "<ISO-8601 timestamp>"
}
```

### Step 0.7: Initialize Pipeline Status

Write `.cli-pipeline/pipeline-status.json`:

```json
{
  "cli_name": "<chosen-name>",
  "repo_path": "<absolute-path>",
  "started_at": "<ISO-8601>",
  "phases": {
    "0_input_classification": { "status": "completed", "completed_at": "<ISO-8601>" },
    "1_auth_recon":           { "status": "pending" },
    "2_api_recon":            { "status": "pending" },
    "3_endpoint_validation":  { "status": "pending" },
    "4_cli_architect":        { "status": "pending" },
    "5_architecture_audit":   { "status": "pending", "iterations": 0 },
    "6_cli_generator":        { "status": "pending" },
    "7_implementation_audit": { "status": "pending", "iterations": 0 },
    "8_skill_ideation":       { "status": "pending" },
    "9_skill_generation":     { "status": "pending" }
  }
}
```

---

## Phase Dispatch Protocol

For every phase (1-9), follow this exact sequence:

1. **Update status**: Read `.cli-pipeline/pipeline-status.json`, set the current phase to `"in_progress"`, write it back.
2. **Dispatch agent**: Use the Agent tool with `subagent_type` set to the agent name. Include in the prompt:
   - The phase number and name
   - Exact input file paths (absolute, using `repo_path` from `input-classification.json`)
   - Exact output file paths
   - The `repo_path` value
   - Any phase-specific parameters (listed per-phase below)
3. **Verify output**: After the agent returns, confirm the expected output file exists using Glob or Read (first few lines only — do NOT load full content into orchestrator context).
4. **Update status**: Set the phase to `"completed"` with `"completed_at": "<ISO-8601>"` in `pipeline-status.json`.

If an agent fails (output file missing or agent reports error), set the phase status to `"failed"` with `"error": "<brief description>"` and stop the pipeline. Report the failure to the user.

---

## Phase 1: Auth Recon

- **Agent:** `auth-recon`
- **Reads:** `.cli-pipeline/input-classification.json`
- **Writes:** `.cli-pipeline/auth-profile.json`
- **Prompt to agent:**
  > You are running Phase 1 (Auth Recon) of the cli-generation pipeline.
  > Read `.cli-pipeline/input-classification.json` for the target API.
  > Write your output to `.cli-pipeline/auth-profile.json`.

After the agent completes, check if `.cli-pipeline/auth-blocked.json` exists. If it does, the agent already prompted the user via AskUserQuestion. Verify that `.cli-pipeline/auth-profile.json` was written after the user interaction. If auth-profile.json is still missing, stop the pipeline and report the auth failure.

---

## Phase 2: API Recon

- **Agent:** `api-recon`
- **Reads:** `.cli-pipeline/input-classification.json`, `.cli-pipeline/auth-profile.json`
- **Writes:** `.cli-pipeline/endpoints.json`
- **Prompt to agent:**
  > You are running Phase 2 (API Recon) of the cli-generation pipeline.
  > Read `.cli-pipeline/input-classification.json` and `.cli-pipeline/auth-profile.json`.
  > Write your output to `.cli-pipeline/endpoints.json`.

---

## Phase 3: Endpoint Validation

- **Agent:** `endpoint-validator`
- **Reads:** `.cli-pipeline/auth-profile.json`, `.cli-pipeline/endpoints.json`
- **Writes:** `.cli-pipeline/validated-endpoints.json`
- **Prompt to agent:**
  > You are running Phase 3 (Endpoint Validation) of the cli-generation pipeline.
  > Read `.cli-pipeline/auth-profile.json` and `.cli-pipeline/endpoints.json`.
  > Write your output to `.cli-pipeline/validated-endpoints.json`.

---

## Phase 4: CLI Architect

- **Agent:** `cli-architect`
- **Reads:** `.cli-pipeline/validated-endpoints.json`, `.cli-pipeline/auth-profile.json`, `.cli-pipeline/input-classification.json`
- **Writes:** `<repo_path>/docs/architecture.md`
- **Prompt to agent:**
  > You are running Phase 4 (CLI Architect) of the cli-generation pipeline.
  > Read `.cli-pipeline/validated-endpoints.json`, `.cli-pipeline/auth-profile.json`, and `.cli-pipeline/input-classification.json`.
  > The CLI repo is at: `<repo_path>`
  > Write your output to `<repo_path>/docs/architecture.md`.
  > Create the docs/ directory if it doesn't exist.

If this is a **retry after Phase 5 audit**, append to the prompt:
  > This is iteration <N> after an architecture audit graded < B.
  > Read the audit findings at `<repo_path>/docs/arch-audit.md` and make targeted revisions to `<repo_path>/docs/architecture.md`.
  > Only fix what the audit identified — do not redesign from scratch.

---

## Phase 5: Architecture Audit (with Loop)

- **Agent:** `architecture-auditor`
- **Reads:** `<repo_path>/docs/architecture.md`
- **Writes:** `<repo_path>/docs/arch-audit.md`
- **Prompt to agent:**
  > You are running Phase 5 (Architecture Audit) of the cli-generation pipeline.
  > Read `.cli-pipeline/input-classification.json` for `repo_path`.
  > Read `<repo_path>/docs/architecture.md`.
  > Write your audit to `<repo_path>/docs/arch-audit.md`.

### Loop Logic

After the agent completes:

1. Read the first 20 lines of `<repo_path>/docs/arch-audit.md` to extract the grade.
2. Parse the letter grade (A, B, C, D, F — with optional +/- modifier).
3. Check the `iterations` count in `pipeline-status.json` for phase `5_architecture_audit`.

**If grade >= B** (i.e., A+, A, A-, B+, B): mark Phase 5 completed, proceed to Phase 6.

**If grade < B AND iterations < 2:**
1. Increment `iterations` in `pipeline-status.json`.
2. Re-dispatch the `cli-architect` agent (Phase 4) with the audit findings appended to the prompt (see Phase 4 retry prompt above).
3. Re-dispatch the `architecture-auditor` agent (Phase 5) to re-audit.
4. Check the grade again. Repeat up to 2 total iterations.

**If grade < B AND iterations >= 2:** Mark Phase 5 completed with a warning. Log:
  > Architecture audit grade is <grade> after 2 iterations. Proceeding with warnings.

---

## Phase 6: CLI Generator

- **Agent:** `cli-generator`
- **Reads:** `<repo_path>/docs/architecture.md`, `.cli-pipeline/validated-endpoints.json`, `.cli-pipeline/input-classification.json`
- **Writes:** `<repo_path>/src/`, `<repo_path>/tests/`, `<repo_path>/package.json` (or equivalent)
- **Prompt to agent:**
  > You are running Phase 6 (CLI Generator) of the cli-generation pipeline.
  > Read `<repo_path>/docs/architecture.md`, `.cli-pipeline/validated-endpoints.json`, and `.cli-pipeline/input-classification.json`.
  > The CLI repo is at: `<repo_path>`
  > The tech stack is: `<tech_stack>` (from input-classification.json)
  > Generate the full CLI using TDD. Write source to `<repo_path>/src/`, tests to `<repo_path>/tests/`.

If this is a **retry after Phase 7 audit**, append to the prompt:
  > This is iteration <N> after an implementation audit graded < B.
  > Read the audit findings at `<repo_path>/docs/impl-audit.md` and make targeted fixes.
  > Do NOT regenerate — only fix what the audit identified.

---

## Phase 7: Implementation Audit (with Loop)

- **Agent:** `implementation-auditor`
- **Reads:** `<repo_path>/` (full CLI repo)
- **Writes:** `<repo_path>/docs/impl-audit.md`
- **Prompt to agent:**
  > You are running Phase 7 (Implementation Audit) of the cli-generation pipeline.
  > Read `.cli-pipeline/input-classification.json` for `repo_path`.
  > Audit the CLI codebase at `<repo_path>/`.
  > Write your audit to `<repo_path>/docs/impl-audit.md`.

### Loop Logic

Same pattern as Phase 5:

1. Read the first 20 lines of `<repo_path>/docs/impl-audit.md` to extract the grade.
2. Parse the letter grade.

**If grade >= B:** Mark Phase 7 completed, proceed to Phase 8.

**If grade < B AND iterations < 2:**
1. Increment `iterations` in `pipeline-status.json` for `7_implementation_audit`.
2. Re-dispatch the `cli-generator` agent (Phase 6) with audit findings in the prompt.
3. Re-dispatch the `implementation-auditor` agent (Phase 7) to re-audit.

**If grade < B AND iterations >= 2:** Mark Phase 7 completed with a warning.

---

## Phase 8: Skill Ideation (with Pause)

- **Agent:** `skill-ideator`
- **Reads:** `.cli-pipeline/validated-endpoints.json`, `<repo_path>/docs/architecture.md`, `<repo_path>/docs/impl-audit.md`
- **Writes:** `<repo_path>/docs/feature-backlog.md`
- **Prompt to agent:**
  > You are running Phase 8 (Skill Ideation) of the cli-generation pipeline.
  > Read `.cli-pipeline/input-classification.json` for `repo_path` and `cli_name`.
  > Read `.cli-pipeline/validated-endpoints.json`, `<repo_path>/docs/architecture.md`, and `<repo_path>/docs/impl-audit.md`.
  > Write your output to `<repo_path>/docs/feature-backlog.md`.

### Pause: User Skill Selection

After the agent completes:

1. Read `<repo_path>/docs/feature-backlog.md`.
2. Extract the feature list with IDs, titles, categories, and priority tiers.
3. Present the backlog to the user using AskUserQuestion with `multiSelect: true`:
   ```
   The skill ideator generated <N> feature ideas across 6 categories.

   P0 (Must-have):
     [1] <title> — <category>
     [2] <title> — <category>

   P1 (Should-have):
     [3] <title> — <category>
     [4] <title> — <category>

   P2/P3 (Nice-to-have):
     [5] <title> — <category>
     ...

   Select features to generate skills for (comma-separated IDs), or:
   - "all" to generate all
   - "p0" to generate P0 only
   - "p0,p1" for P0 + P1
   - Type custom skill ideas on a new line
   - "skip" to skip skill generation entirely
   ```
4. Parse the user's response into a list of selected feature IDs and any custom additions.
5. If the user selects "skip", mark Phase 8 completed and Phase 9 as "skipped", then jump to Completion.
6. Store the selections for the Phase 9 dispatch.

---

## Phase 9: Skill Generation

- **Agent:** `skill-generator`
- **Reads:** `<repo_path>/`, `<repo_path>/docs/feature-backlog.md`, `<repo_path>/docs/architecture.md`
- **Writes:** `<repo_path>/skills/`
- **Prompt to agent:**
  > You are running Phase 9 (Skill Generation) of the cli-generation pipeline.
  > Read `.cli-pipeline/input-classification.json` for `repo_path` and `cli_name`.
  > Read `<repo_path>/docs/feature-backlog.md` and `<repo_path>/docs/architecture.md`.
  > Read the CLI source at `<repo_path>/src/` to document actual implementations.
  > Generate skills for these selected features: <comma-separated feature IDs and titles>
  > <If user added custom ideas, list them here>
  > Write skill files to `<repo_path>/skills/`.

---

## Completion

After Phase 9 completes (or Phase 8 if skills were skipped):

1. Update `pipeline-status.json` with `"completed_at"` at the top level.

2. Collect summary data:
   - Architecture audit grade: read first line of `<repo_path>/docs/arch-audit.md`
   - Implementation audit grade: read first line of `<repo_path>/docs/impl-audit.md`
   - Skill count: count directories in `<repo_path>/skills/`
   - Endpoint coverage: read `summary` from `.cli-pipeline/validated-endpoints.json`

3. Present the summary to the user:
   ```
   CLI generation complete for <cli_name>.

   Repo: <repo_path>
   Architecture audit: <grade>
   Implementation audit: <grade>
   Endpoints: <valid>/<total> validated
   Skills generated: <count>
   ```

4. Use AskUserQuestion to ask:
   > Push to GitHub as a new private repo?
   > - Yes (creates github.com/<user>/<cli_name>)
   > - No (keep local only)

5. If yes, run from the CLI repo:
   ```bash
   cd "<repo_path>"
   gh repo create "<cli_name>" --private --source=. --push
   ```
   Capture the repo URL with `gh repo view --json url -q '.url'`.

6. Final message:
   ```
   Done. <cli_name> is ready at <repo_path>.
   <If pushed: GitHub: <repo_url>>
   Run: cd <repo_path> && <install command based on tech stack>
   ```
