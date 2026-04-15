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
7. **Rebuild task UI on resume:** Create tasks for all 10 phases using TaskCreate (see Progress Tracking below). Then immediately mark completed phases as `completed` via TaskUpdate. This rebuilds the visual progress list from durable state. If TaskCreate is unavailable, skip this step.

---

## Progress Tracking

Use **dual tracking** for pipeline progress:

1. **`pipeline-status.json`** — durable JSON file for cross-session resume. This is the source of truth. Always updated.
2. **TaskCreate / TaskUpdate** — visual task list shown in the Claude Code status line. Additive UX only.

TaskCreate and TaskUpdate are built-in Claude Code tools. They may not exist in other runtimes (Copilot CLI, etc.). **If TaskCreate is unavailable, skip all task UI calls silently** — both TaskCreate and TaskUpdate come as a pair in Claude Code, so checking for one is sufficient. The pipeline works entirely through `pipeline-status.json` — the task UI is a visual bonus, never a requirement.

### Task creation pattern

After writing `pipeline-status.json` (Step 0.7), create 10 tasks:

| Task subject | activeForm |
|---|---|
| Phase 0: Classify input | Classifying input... |
| Phase 1: Auth recon | Discovering auth mechanism... |
| Phase 2: API recon | Mapping API surface... |
| Phase 3: Validate endpoints | Validating endpoints... |
| Phase 4: Design CLI architecture | Designing CLI architecture... |
| Phase 5: Audit architecture | Auditing architecture... |
| Phase 6: Generate CLI (TDD) | Generating CLI code... |
| Phase 7: Audit implementation | Auditing implementation... |
| Phase 8: Ideate skills | Brainstorming skill ideas... |
| Phase 9: Generate skills | Generating SKILL.md files... |

Mark Phase 0 as `completed` immediately (it just ran).

### Task update pattern

For each phase dispatch:
- **Before dispatch:** `TaskUpdate` → status `in_progress`
- **After completion:** `TaskUpdate` → status `completed`
- **On failure:** Leave as `in_progress` (the failure message to the user provides context)

### Audit loop task updates

When Phase 5 or Phase 7 loops back:
- Set the audit task back to `in_progress` with activeForm "Re-auditing architecture (iteration 2)..."
- Set the upstream task (Phase 4 or 6) back to `in_progress` with activeForm "Revising architecture..." or "Fixing implementation..."

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

### Step 0.7b: Create Phase Outputs Directory

Create the directory for immutable per-phase output manifests:

```bash
mkdir -p .cli-pipeline/phase-outputs
```

Each phase will write a compact, immutable JSON manifest here after completion. Later phases read these ~200-500 token summaries instead of re-parsing large artifact files.

### Step 0.8: Create Visual Task List

Create tasks for visual progress tracking (see Progress Tracking section). Use TaskCreate to create one task per phase with the subjects and activeForm labels from the table above. Each TaskCreate call returns a task ID — keep these in memory as a phase-to-taskId map (e.g., `phase_tasks["1_auth_recon"] = "task-3"`). Use these IDs for all subsequent TaskUpdate calls.

Immediately mark the Phase 0 task as `completed` via TaskUpdate using its returned task ID.

If TaskCreate is unavailable, skip this step — `pipeline-status.json` handles all tracking. Set a flag (e.g., `task_ui_enabled = false`) so all subsequent TaskUpdate calls are also skipped.

---

## Phase Dispatch Protocol

For every phase (1-9), follow this exact sequence:

1. **Update status**: Read `.cli-pipeline/pipeline-status.json`, set the current phase to `"in_progress"`, write it back. Also `TaskUpdate` the corresponding task to `in_progress` (skip if TaskCreate was unavailable at pipeline start).
2. **Dispatch agent**: Use the Agent tool with `subagent_type` set to the agent name. Include in the prompt:
   - The phase number and name
   - Exact input file paths (absolute, using `repo_path` from `input-classification.json`)
   - Exact output file paths
   - The `repo_path` value
   - Any phase-specific parameters (listed per-phase below)
3. **Verify output**: After the agent returns, confirm the expected output file exists using Glob or Read (first few lines only — do NOT load full content into orchestrator context).
3b. **Write phase output manifest**: Read only the minimal fields needed from the phase's primary artifact (first 10-20 lines). Write a manifest to `.cli-pipeline/phase-outputs/phase-NN-<name>.json`:

```json
{
  "schema_version": 1,
  "phase": "<phase_name>",
  "timestamp": "<ISO 8601>",
  "outputs": {}
}
```

The `outputs` object contains phase-specific summary fields (defined per-phase below). For retryable phases (5, 7), the manifest is overwritten on each iteration — the latest version is always the current truth.

4. **Update status**: Set the phase to `"completed"` with `"completed_at": "<ISO-8601>"` in `pipeline-status.json`. Also `TaskUpdate` the corresponding task to `completed` (skip if TaskCreate was unavailable at pipeline start).

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

Write `.cli-pipeline/phase-outputs/phase-01-auth.json`:
- Read `auth_type`, `credential_source`, and `discovery_method` from `auth-profile.json` (first 10 lines only)
- `"outputs": { "auth_type": "<type>", "credential_source": "<source>", "discovery_method": "<method>" }`

---

## Phase 2: API Recon

- **Agent:** `api-recon`
- **Reads:** `.cli-pipeline/input-classification.json`, `.cli-pipeline/auth-profile.json`
- **Writes:** `.cli-pipeline/endpoints.json`
- **Prompt to agent:**
  > You are running Phase 2 (API Recon) of the cli-generation pipeline.
  > Read `.cli-pipeline/input-classification.json` and `.cli-pipeline/auth-profile.json`.
  > Write your output to `.cli-pipeline/endpoints.json`.

Write `.cli-pipeline/phase-outputs/phase-02-api.json`:
- Read `coverage` and `service` fields from `endpoints.json` (do NOT load the full endpoint list)
- `"outputs": { "endpoint_count": N, "base_url": "<url>", "spec_source": "<source>" }`

---

## Phase 3: Endpoint Validation

- **Agent:** `endpoint-validator`
- **Reads:** `.cli-pipeline/auth-profile.json`, `.cli-pipeline/endpoints.json`
- **Writes:** `.cli-pipeline/validated-endpoints.json`
- **Prompt to agent:**
  > You are running Phase 3 (Endpoint Validation) of the cli-generation pipeline.
  > Read `.cli-pipeline/auth-profile.json` and `.cli-pipeline/endpoints.json`.
  > Write your output to `.cli-pipeline/validated-endpoints.json`.

Write `.cli-pipeline/phase-outputs/phase-03-validation.json`:
- Read only the `summary` block from `validated-endpoints.json`
- `"outputs": { "valid": N, "invalid": N, "unreachable": N, "auth_blocked": N, "skipped_destructive": N }`

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
  > Also read the relevant `.cli-pipeline/phase-outputs/phase-NN-*.json` files for compact summaries of prior phases. Use these for context instead of re-reading large artifact files when possible.

If this is a **retry after Phase 5 audit**, append to the prompt:
  > This is iteration <N> after an architecture audit graded < B.
  > Read the audit findings at `<repo_path>/docs/arch-audit.md` and make targeted revisions to `<repo_path>/docs/architecture.md`.
  > Only fix what the audit identified — do not redesign from scratch.

Write `.cli-pipeline/phase-outputs/phase-04-architect.json`:
- Read first 30 lines of `architecture.md` to extract command count and structure
- `"outputs": { "command_count": N, "helper_count": N, "resource_groups": ["<group1>", "<group2>"] }`

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
  > Also read the relevant `.cli-pipeline/phase-outputs/phase-NN-*.json` files for compact summaries of prior phases. Use these for context instead of re-reading large artifact files when possible.

### Loop Logic

After the agent completes:

1. Read the first 20 lines of `<repo_path>/docs/arch-audit.md` to extract the grade.
2. Parse the letter grade (A, B, C, D, F — with optional +/- modifier).
3. Check the `iterations` count in `pipeline-status.json` for phase `5_architecture_audit`.

**If grade >= B** (i.e., A+, A, A-, B+, B): mark Phase 5 completed, proceed to Phase 6.

**If grade < B AND iterations < 2:**
1. Increment `iterations` in `pipeline-status.json`.
2. Update task UI: `TaskUpdate` the Phase 4 task back to `in_progress` with activeForm "Revising architecture...". `TaskUpdate` the Phase 5 task back to `in_progress` with activeForm "Re-auditing architecture (iteration <N+1>)..." where N is the current iteration count.
3. Re-dispatch the `cli-architect` agent (Phase 4) with the audit findings appended to the prompt (see Phase 4 retry prompt above).
4. Re-dispatch the `architecture-auditor` agent (Phase 5) to re-audit.
5. Check the grade again. Repeat up to 2 total iterations.

**If grade < B AND iterations >= 2:** Mark Phase 5 completed with a warning. Log:
  > Architecture audit grade is <grade> after 2 iterations. Proceeding with warnings.

Write `.cli-pipeline/phase-outputs/phase-05-arch-audit.json`:
- Read first 5 lines of `arch-audit.md` for grade
- `"outputs": { "grade": "<letter>", "score": N, "iterations": N }`

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
  > Also read the relevant `.cli-pipeline/phase-outputs/phase-NN-*.json` files for compact summaries of prior phases. Use these for context instead of re-reading large artifact files when possible.

If this is a **retry after Phase 7 audit**, append to the prompt:
  > This is iteration <N> after an implementation audit graded < B.
  > Read the audit findings at `<repo_path>/docs/impl-audit.md` and make targeted fixes.
  > Do NOT regenerate — only fix what the audit identified.

Write `.cli-pipeline/phase-outputs/phase-06-generator.json`:
- Count files in `src/` and `tests/` using Glob
- `"outputs": { "source_files": N, "test_files": N, "tests_passed": N }`

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
  > Also read the relevant `.cli-pipeline/phase-outputs/phase-NN-*.json` files for compact summaries of prior phases. Use these for context instead of re-reading large artifact files when possible.

### Loop Logic

Same pattern as Phase 5:

1. Read the first 20 lines of `<repo_path>/docs/impl-audit.md` to extract the grade.
2. Parse the letter grade.

**If grade >= B:** Mark Phase 7 completed, proceed to Phase 8.

**If grade < B AND iterations < 2:**
1. Increment `iterations` in `pipeline-status.json` for `7_implementation_audit`.
2. Update task UI: `TaskUpdate` the Phase 6 task back to `in_progress` with activeForm "Fixing implementation...". `TaskUpdate` the Phase 7 task back to `in_progress` with activeForm "Re-auditing implementation (iteration <N+1>)..." where N is the current iteration count.
3. Re-dispatch the `cli-generator` agent (Phase 6) with audit findings in the prompt.
4. Re-dispatch the `implementation-auditor` agent (Phase 7) to re-audit.

**If grade < B AND iterations >= 2:** Mark Phase 7 completed with a warning.

Write `.cli-pipeline/phase-outputs/phase-07-impl-audit.json`:
- Read first 10 lines of `impl-audit.md` for grade and test results
- `"outputs": { "grade": "<letter>", "score": N, "tests_passed": N, "tests_failed": N, "iterations": N }`

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
  > Also read the relevant `.cli-pipeline/phase-outputs/phase-NN-*.json` files for compact summaries of prior phases. Use these for context instead of re-reading large artifact files when possible.
  >
  > IMPORTANT: You are identifying SKILL DOMAINS — not brainstorming code changes.
  > A skill is a SKILL.md file that teaches an AI agent when and how to compose
  > CLI commands for a specific workflow domain. Skills cluster commands by user
  > intent ("how's my body?" not "sleep-service + hr-service").
  >
  > Do NOT propose code changes (caching, new flags, middleware) as skills.
  > Those belong in a separate CLI Enhancement Backlog section of the output.
  >
  > Target: 4-8 skill domains for multi-service CLIs (3+ resource groups),
  > 2-4 for single-service (2 resource groups), 1 shared skill for single-resource (1 group).

Write `.cli-pipeline/phase-outputs/phase-08-ideation.json`:
- Count skill domains and enhancement backlog items from `feature-backlog.md`
- `"outputs": { "total_skills": N, "total_enhancements": N, "p0_count": N, "p1_count": N }`

### Pause: User Skill Selection

After the agent completes:

1. Read `<repo_path>/docs/feature-backlog.md`.
2. Extract the skill domain list with IDs, names, intent clusters, draft triggers, and priority tiers.
3. Present the skill domains to the user using AskUserQuestion with `multiSelect: true`:
   ```
   The skill ideator identified <N> skill domains for <cli_name>.

   Skill Domains:
     [1] <skill-name> — <intent cluster> (P0)
         Use when: <draft trigger>
     [2] <skill-name> — <intent cluster> (P1)
         Use when: <draft trigger>
     ...

   CLI Enhancement Backlog: <M> code changes (routed to impl-audit, not skill generation)

   Select skill domains to generate SKILL.md files for:
   - "all" to generate all
   - "1,2,3" for specific domains
   - "p0" for P0 only, "p0,p1" for P0 + P1
   - Type custom skill ideas on a new line
   - "skip" to skip skill generation entirely
   ```
4. Parse the user's response into a list of selected skill domain IDs and any custom additions.
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
  > Generate SKILL.md files for these selected skill domains: <comma-separated domain IDs and names>
  > <If user added custom ideas, list them here>
  > Write skill files to `<repo_path>/skills/`.
  > Also read the relevant `.cli-pipeline/phase-outputs/phase-NN-*.json` files for compact summaries of prior phases. Use these for context instead of re-reading large artifact files when possible.
  >
  > MUST invoke `superpowers:skill-creator` before generating any SKILL.md files.
  > Each skill must follow the naming convention: <cli>-shared, <cli>-<domain>,
  > recipe-<workflow>, persona-<role>.

Write `.cli-pipeline/phase-outputs/phase-09-skills.json`:
- Count directories in `<repo_path>/skills/` using Glob
- `"outputs": { "skill_count": N, "skills": ["<skill1>", "<skill2>"] }`

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

   If the CLI Enhancement Backlog in `feature-backlog.md` has items, mention:
   ```
   Enhancement backlog: <N> code changes identified (flags, middleware, etc.)
   These are in <repo_path>/docs/feature-backlog.md for the next build cycle.
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
