# Token Cost Optimization Implementation Plan (v2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Review history:** This plan was reviewed by 3 independent Principal Engineer models (GPT 5.4: D, Claude Opus 4.6: C, Goldeneye: D). v2 incorporates all accepted findings. See [Review Decisions](#review-decisions) for the full decision log.

**Goal:** Reduce cli-generation pipeline token cost from ~$184/run to ~$80-110/run (conservative) by optimizing context management, model selection, and subagent communication.

**Architecture:** Six changes organized into 3 dependent workstreams, rolled out in 3 waves with measurement gates between each. Two tasks from v1 were killed (see [Removed Tasks](#removed-tasks)).

**Tech Stack:** Markdown (agent/skill/command definitions), JSON (pipeline artifacts)

**Evidence base:** Session `aff72279-9530-450b-a0d6-87ce2456348e` — Garmin CLI pipeline, 11.4M input tokens, $184 total cost.

---

## Effort / ROI Matrix

| Task | Effort | Savings (est.) | ROI | Priority |
|---|---|---|---|---|
| Task 1: Prompt Caching Spike | 2-4 hours | $0-80 (unknown) | Must-do (gates everything) | **P0 — spike** |
| Task 4: Sonnet for Audits | 15 min | ~$16/run | Extreme | **P0 — trivial** |
| Task 3: Return Summaries | 2-3 hours | ~$10-15/run | High | **P1** |
| Task 6: Canonical Checklist Ref | 1-2 hours | ~$5-8/run | High | **P1** |
| Task 7: Immutable Phase Artifacts | 3-4 hours | ~$3-5/run | Medium | **P2** |
| Task 5: Parallel Generator | 6-8 hours | ~$10-15/run | Medium | **P2** |

---

## Workstream Model

These are NOT independent tasks. They interact on savings and behavior.

### Workstream A: Context Assembly & Caching
- Task 1 (Prompt Caching Spike)
- Task 3 (Return Summaries)
- Task 6 (Canonical Checklist Reference)
- Task 7 (Immutable Phase Artifacts)

*Interaction:* If caching delivers high hit rates, Tasks 3/6/7 save less on repeated context (cached tokens are cheap). If caching is unavailable, these tasks become the primary savings mechanism.

### Workstream B: Model Routing
- Task 4 (Sonnet for Audits)

*Interaction:* Independent of caching. Savings are deterministic based on per-token pricing.

### Workstream C: Execution Topology
- Task 5 (Parallel Generator)

*Interaction:* Changes artifact shape, which affects how Task 3 summaries work for the generator phase.

---

## Rollout Waves

### Wave 0: Prerequisites (before any optimization)

- [ ] **Step 0.1: Establish quality baseline**

Run the current (unmodified) pipeline on 3 representative inputs:
1. **Small API** — ≤5 resource groups, REST, public docs (e.g., a simple CRUD API)
2. **Medium API** — 10-15 resource groups, mixed auth (e.g., Garmin Connect subset)
3. **Large SDK** — 20+ resource groups, SDK-based input (e.g., full Garmin Connect)

For each run, capture:
- Total token count (input + output) per phase
- Total cost
- Generated CLI output (all files → golden snapshot)
- Audit grades and findings
- Test pass/fail counts

Store golden snapshots in `.cli-pipeline/golden/` with run metadata.

**Quality gate definition:** An optimization passes if:
- All commands from baseline are still present in output
- Argument types and names match baseline
- Help text is coherent (no truncation or garbage)
- Audit grades don't drop more than one notch (e.g., B+ → B is ok, B+ → C is not)
- All tests that passed in baseline still pass

- [ ] **Step 0.2: Instrument token tracking**

Add per-phase token counting to pipeline output. After each phase completes, log:
```json
{
  "phase": "<name>",
  "input_tokens": "<N>",
  "output_tokens": "<N>",
  "cache_read_tokens": "<N>",
  "cache_creation_tokens": "<N>",
  "model": "<model_used>",
  "cost_usd": "<N>"
}
```

This is required for the waterfall savings model — you need per-phase cost attribution.

---

### Wave 1: Spike + Trivial Win

**Tasks:** 1 (caching spike) + 4 (Sonnet for audits)
**Gate:** Measure actual savings. Re-estimate Wave 2/3 tasks based on caching results.

---

### Task 1: Investigate and Enable Prompt Caching (#7)

> **Note:** This is a spike — the single most important task. Its outcome reshapes the ROI of every other task. Do this FIRST. Do not proceed to Wave 2 until findings are documented.

> **Subtasks:** Split into 3 phases: (1A) Instrumentation & verification, (1B) Cache-key stabilization, (1C) Enablement. Only 1C gets savings credit, and only after hit-rate data exists.

**Files:**
- Investigate: Claude Code harness source (how Agent tool constructs API calls)
- Investigate: `~/.claude/settings.json` (harness config)
- Investigate: Anthropic API docs for prompt caching requirements

- [ ] **Step 1A.1: Check Anthropic prompt caching requirements**

Search Anthropic docs for prompt caching activation requirements. Key questions:
- Does caching require explicit `cache_control` breakpoints in the message array?
- Does the Claude Code Agent tool set these breakpoints?
- Is there a minimum token threshold for caching to activate?
- How stable must the prompt prefix be for cache hits?

Run:
```bash
claude --version
```
Expected: Version info to confirm Claude Code version.

- [ ] **Step 1A.2: Check if caching is disabled in settings**

```bash
cat ~/.claude/settings.json | grep -i cache
```
Expected: Check for any `cache` or `prompt_caching` settings.

- [ ] **Step 1A.3: Analyze session JSONL for cache fields**

```bash
head -5 ~/.claude/projects/C--Users-kalebcole--agents-notch/aff72279-9530-450b-a0d6-87ce2456348e.jsonl | python3 -c "import sys,json; [print(json.dumps({k:v for k,v in json.loads(l).items() if 'cache' in str(k).lower() or 'usage' in str(k).lower()}, indent=2)) for l in sys.stdin if 'usage' in l]"
```
Expected: See whether `cache_creation_input_tokens` and `cache_read_input_tokens` are present and always 0.

- [ ] **Step 1A.4: Measure prompt prefix stability**

Across the session JSONL, check whether the system prompt prefix is identical across turns. If it varies (e.g., dynamic context injection changes it), cache hit rates will be low regardless of enablement.

- [ ] **Step 1B.1: Stabilize cache keys (if needed)**

If prompts vary across turns, identify what's changing and whether it can be made static. Common culprits:
- Timestamp injection in system prompts
- Dynamic context loading (daily files, memory)
- Tool result accumulation changing prefix alignment

- [ ] **Step 1C.1: Enable caching and measure hit rates**

If caching is available and not enabled, enable it. Run a test pipeline and measure:
- `cache_read_input_tokens` / `total_input_tokens` = hit rate
- Cost delta vs. baseline

**Decision gate:** Document findings on GitHub issue #7:
- Is caching harness-level or plugin-controllable?
- What's the measured hit rate?
- What's the actual cost savings (not estimated)?
- Does this change the ROI for Wave 2/3 tasks?

```bash
cd ~/repos/cli-generation && gh issue comment 7 --body "## Investigation Findings

<findings here>"
```

- [ ] **Step 1C.2: Re-estimate remaining tasks**

With actual caching data:
- If hit rate > 70%: Tasks 3, 6, 7 save less (cached repeated tokens are cheap). Adjust estimates downward.
- If hit rate < 30% or unavailable: Tasks 3, 6, 7 become the primary cost reduction mechanism. Prioritize them.
- Update the waterfall savings model with real numbers.

- [ ] **Step 1C.3: Commit investigation notes**

```bash
cd ~/repos/cli-generation
git add -A
git commit -m "docs: prompt caching investigation for #7"
```

---

### Task 4: Use Sonnet for Audit Phases (#10)

> **Context:** Agent frontmatter supports a `model` field that overrides the parent session's model. Adding `model: sonnet` to the audit agents drops their cost from $15/MTok to $3/MTok input. This is deterministic savings — independent of caching.

> **Effort:** 15 minutes. **Savings:** ~$16/run. **ROI:** Extreme.

**Files:**
- Modify: `agents/architecture-auditor.md:1-11` (add model to frontmatter)
- Modify: `agents/implementation-auditor.md:1-11` (add model to frontmatter)

- [ ] **Step 1: Add model to architecture-auditor frontmatter**

In `agents/architecture-auditor.md`, change the frontmatter from:

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

To:

```yaml
---
description: >-
  Architecture auditor subagent for the cli-generation pipeline. Grades CLI architecture
  against the 14-point quality checklist. Reads architecture.md, writes arch-audit.md.
  If grade < B, provides specific findings for the architect to fix.
model: sonnet
tools:
  - Read
  - Write
  - Glob
  - Grep
---
```

- [ ] **Step 2: Add model to implementation-auditor frontmatter**

In `agents/implementation-auditor.md`, change the frontmatter from:

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

To:

```yaml
---
description: >-
  Implementation auditor subagent for the cli-generation pipeline. Grades the built CLI
  against the 14-point quality checklist. Reads the CLI repo codebase, writes impl-audit.md.
  If grade < B, provides specific findings for targeted fixes.
model: sonnet
tools:
  - Read
  - Write
  - Bash
  - Glob
  - Grep
---
```

- [ ] **Step 3: Verify frontmatter is valid YAML**

```bash
cd ~/repos/cli-generation
for f in agents/architecture-auditor.md agents/implementation-auditor.md; do
  echo "=== $f ==="
  head -12 "$f"
  echo
done
```
Expected: Both files show `model: sonnet` between `description` and `tools`.

- [ ] **Step 4: Run quality gate**

Run the pipeline on the Small API golden input. Compare audit grades and findings against baseline. If audit quality drops more than one grade notch, revert.

- [ ] **Step 5: Commit**

```bash
cd ~/repos/cli-generation
git add agents/architecture-auditor.md agents/implementation-auditor.md
git commit -m "perf: use sonnet model for audit phases (#10)

Architecture and implementation auditors are checklist-grading tasks
that don't require Opus-level reasoning. Sonnet at $3/MTok input
saves ~$16/run vs Opus at $15/MTok."
```

---

### Wave 1 Gate

Before proceeding to Wave 2:
- [ ] Document Task 1 findings (caching available? hit rate? actual savings?)
- [ ] Document Task 4 savings (measured, not estimated)
- [ ] Re-estimate Wave 2/3 task savings using waterfall model
- [ ] Update this plan with actual numbers

---

### Wave 2: Subagent Contract Compression

**Tasks:** 3 (Return Summaries) + 6 (Canonical Checklist Reference)
**Gate:** Measure cumulative savings. Validate quality against golden files.

---

### Task 3: Summarize Subagent Results Before Returning (#9)

> **Context:** When a subagent finishes, its full output flows back to the orchestrator as a tool result. This adds a "Return Summary" section to each agent definition instructing it to print a compact JSON summary as its final output — which is what the orchestrator sees.

> **Effort:** 2-3 hours. **Savings:** ~$10-15/run (less if caching is active). **ROI:** High.

**Files:**
- Modify: `agents/auth-recon.md` (append summary section)
- Modify: `agents/api-recon.md` (append summary section)
- Modify: `agents/endpoint-validator.md` (append summary section)
- Modify: `agents/cli-architect.md` (append summary section)
- Modify: `agents/architecture-auditor.md` (append summary section)
- Modify: `agents/cli-generator.md` (append summary section)
- Modify: `agents/implementation-auditor.md` (append summary section)
- Modify: `agents/skill-ideator.md` (append summary section)

**Schema (v2 — includes `schema_version` and `warnings`):**

All return summaries use this base schema:
```json
{
  "schema_version": 1,
  "phase": "<phase_name>",
  "status": "completed",
  "artifact": "<path to primary output file>",
  "summary": "<one sentence describing what was accomplished>",
  "warnings": []
}
```

The `warnings` array captures non-fatal issues the orchestrator should know about (e.g., `"3 endpoints returned 401 — may need auth scope expansion"`). Empty array if no warnings.

Phase-specific fields are added alongside the base fields (not nested).

- [ ] **Step 1: Add return summary to auth-recon.md**

Append after the `## Output` section at the end of `agents/auth-recon.md`:

```markdown

## Return Summary

Your final message back to the orchestrator MUST be ONLY this compact JSON (no prose, no explanation):

```json
{
  "schema_version": 1,
  "phase": "auth_recon",
  "status": "completed",
  "artifact": ".cli-pipeline/auth-profile.json",
  "summary": "<one sentence: auth type discovered and credential source>",
  "warnings": []
}
```

If auth was blocked and required user input, set status to `"completed_with_interaction"`.
If auth discovery failed entirely, set status to `"failed"` and add `"error": "<reason>"`.
Add any non-fatal issues to the `warnings` array (e.g., `"OAuth token expired during discovery"`).
```

- [ ] **Step 2: Add return summary to api-recon.md**

Append after the `## Output` section at the end of `agents/api-recon.md`:

```markdown

## Return Summary

Your final message back to the orchestrator MUST be ONLY this compact JSON (no prose, no explanation):

```json
{
  "schema_version": 1,
  "phase": "api_recon",
  "status": "completed",
  "artifact": ".cli-pipeline/endpoints.json",
  "summary": "<one sentence: N endpoints mapped across M resource groups from <source>>",
  "warnings": []
}
```
```

- [ ] **Step 3: Add return summary to endpoint-validator.md**

Append after the `## Output` section at the end of `agents/endpoint-validator.md`:

```markdown

## Return Summary

Your final message back to the orchestrator MUST be ONLY this compact JSON (no prose, no explanation):

```json
{
  "schema_version": 1,
  "phase": "endpoint_validation",
  "status": "completed",
  "artifact": ".cli-pipeline/validated-endpoints.json",
  "summary": "Validated: <N> valid, <N> invalid, <N> unreachable, <N> auth_blocked, <N> skipped",
  "warnings": []
}
```
```

- [ ] **Step 4: Add return summary to cli-architect.md**

Read `agents/cli-architect.md` first, then append after its `## Output` section:

```markdown

## Return Summary

Your final message back to the orchestrator MUST be ONLY this compact JSON (no prose, no explanation):

```json
{
  "schema_version": 1,
  "phase": "cli_architect",
  "status": "completed",
  "artifact": "<repo_path>/docs/architecture.md",
  "summary": "<one sentence: N commands, M helpers, auth design, key architectural decisions>",
  "warnings": []
}
```
```

- [ ] **Step 5: Add return summary to architecture-auditor.md**

Append after the `## Output` section at the end of `agents/architecture-auditor.md`:

```markdown

## Return Summary

Your final message back to the orchestrator MUST be ONLY this compact JSON (no prose, no explanation):

```json
{
  "schema_version": 1,
  "phase": "architecture_audit",
  "status": "completed",
  "artifact": "<repo_path>/docs/arch-audit.md",
  "grade": "<letter grade>",
  "summary": "<one sentence: grade and top finding>",
  "warnings": []
}
```
```

- [ ] **Step 6: Add return summary to cli-generator.md**

Append after the `## Output` section at the end of `agents/cli-generator.md`:

```markdown

## Return Summary

Your final message back to the orchestrator MUST be ONLY this compact JSON (no prose, no explanation):

```json
{
  "schema_version": 1,
  "phase": "cli_generator",
  "status": "completed",
  "artifact": "<repo_path>/src/",
  "summary": "<one sentence: N source files, M test files, all tests passing>",
  "test_result": "<N passed, 0 failed>",
  "warnings": []
}
```
```

- [ ] **Step 7: Add return summary to implementation-auditor.md**

Append after the `## Output` section at the end of `agents/implementation-auditor.md`:

```markdown

## Return Summary

Your final message back to the orchestrator MUST be ONLY this compact JSON (no prose, no explanation):

```json
{
  "schema_version": 1,
  "phase": "implementation_audit",
  "status": "completed",
  "artifact": "<repo_path>/docs/impl-audit.md",
  "grade": "<letter grade>",
  "summary": "<one sentence: grade, test results, top finding>",
  "test_result": "<N passed, N failed>",
  "warnings": []
}
```
```

- [ ] **Step 8: Add return summary to skill-ideator.md**

Append after the `## Output` section at the end of `agents/skill-ideator.md`:

```markdown

## Return Summary

Your final message back to the orchestrator MUST be ONLY this compact JSON (no prose, no explanation):

```json
{
  "schema_version": 1,
  "phase": "skill_ideation",
  "status": "completed",
  "artifact": "<repo_path>/docs/feature-backlog.md",
  "summary": "<one sentence: N features across 6 categories, M P0, N P1>",
  "warnings": []
}
```
```

- [ ] **Step 9: Verify all 8 agent files have the Return Summary section**

```bash
cd ~/repos/cli-generation
for f in agents/*.md; do echo "=== $f ==="; grep -c "Return Summary" "$f"; done
```
Expected: Each file shows `1` (except `skill-generator.md` which wasn't modified).

- [ ] **Step 10: Run quality gate**

Run pipeline on Small API golden input. Verify orchestrator still makes correct phase-transition decisions with summary-only context.

- [ ] **Step 11: Commit**

```bash
cd ~/repos/cli-generation
git add agents/auth-recon.md agents/api-recon.md agents/endpoint-validator.md agents/cli-architect.md agents/architecture-auditor.md agents/cli-generator.md agents/implementation-auditor.md agents/skill-ideator.md
git commit -m "perf: add compact return summaries to all pipeline agents (#9)

Each agent now returns a structured JSON summary (schema v1) as its
final message instead of prose. Includes schema_version and warnings[]
for forward compatibility. Reduces orchestrator context accumulation
by ~50K tokens per pipeline run."
```

---

### Task 6: Use Canonical Checklist Reference in Audit Phases (#12)

> **Context:** The audit agents re-read `architecture.md` and the quality checklist on every scoring cycle. Rather than inlining the checklist into each auditor (which creates duplicate copies to maintain — shotgun surgery), we keep one canonical checklist and reference it.

> **Effort:** 1-2 hours. **Savings:** ~$5-8/run. **ROI:** High.

> **Design decision (from review):** v1 proposed inlining the checklist into both auditors. GPT 5.4 flagged this as Shotgun Surgery — if the checklist changes, you must update 3 places. Instead, we keep `skills/cli-audit/references/quality-checklist.md` as the single source of truth and instruct auditors to read it once at the start.

**Files:**
- Modify: `agents/architecture-auditor.md` (replace cli-audit skill invocation with direct file read)
- Modify: `agents/implementation-auditor.md` (replace cli-audit skill invocation with direct file read)
- No changes to: `skills/cli-audit/references/quality-checklist.md` (canonical source)

- [ ] **Step 1: Update architecture-auditor to read checklist directly**

In `agents/architecture-auditor.md`, find the section referencing the cli-audit skill:

```markdown
2. Invoke the `cli-audit` skill. Apply it to the architecture document (not a codebase). Grade the design intent: does the architecture *describe* a CLI that would pass all 14 checks if built as specified?
```

Replace with:

```markdown
2. Read `skills/cli-audit/references/quality-checklist.md` once at the start. Do NOT invoke the `cli-audit` skill — read the checklist file directly. Grade the design intent: does the architecture *describe* a CLI that would pass all 14 checks if built as specified?
```

- [ ] **Step 2: Add file-read strategy to architecture-auditor**

After the Execution heading (before step 1), add:

```markdown
**File read strategy:** Read `architecture.md` and `quality-checklist.md` once at the start. Do NOT re-read them between checklist items. Score all 14 checks from a single read pass, then write the audit report.
```

- [ ] **Step 3: Update implementation-auditor similarly**

In `agents/implementation-auditor.md`, find:

```markdown
2. Invoke the `cli-audit` skill. The scan prompt from the skill's Step 1 is your starting point — dispatch it against the actual codebase.
```

Replace with:

```markdown
2. Read `skills/cli-audit/references/quality-checklist.md` once at the start. Do NOT invoke the `cli-audit` skill — read the checklist file directly and scan the actual codebase against it.
```

- [ ] **Step 4: Add file-read strategy to implementation-auditor**

After the Execution heading (before step 1), add:

```markdown
**File read strategy:** Read the codebase and `quality-checklist.md` once at the start. Do NOT re-read files between checklist items. Score all 14 checks from a single read pass, then write the audit report.
```

- [ ] **Step 5: Verify changes**

```bash
cd ~/repos/cli-generation
grep -c "Do NOT invoke the \`cli-audit\` skill" agents/architecture-auditor.md agents/implementation-auditor.md
grep -c "File read strategy" agents/architecture-auditor.md agents/implementation-auditor.md
```
Expected: Both files show `1` for each grep.

- [ ] **Step 6: Run quality gate**

Run pipeline on Small API golden input. Compare audit grades against baseline. Verify the auditor still finds the same issues.

- [ ] **Step 7: Commit**

```bash
cd ~/repos/cli-generation
git add agents/architecture-auditor.md agents/implementation-auditor.md
git commit -m "perf: use canonical checklist reference in audit agents (#12)

Eliminates redundant cli-audit skill invocations and repeated file
reads. Auditors now read quality-checklist.md directly once at start
instead of invoking the skill. Single source of truth maintained."
```

---

### Wave 2 Gate

Before proceeding to Wave 3:
- [ ] Measure cumulative savings (Wave 1 + Wave 2)
- [ ] Compare generated CLI output against golden files for all 3 inputs
- [ ] Document actual vs. estimated savings per task
- [ ] Re-estimate Wave 3 tasks if needed

---

### Wave 3: Topology & Handoffs

**Tasks:** 5 (Parallel Generator) + 7 (Immutable Phase Artifacts)
**Gate:** Final measurement. Update savings waterfall with actuals.

---

### Task 7: Pass Compact Context via Immutable Phase Artifacts (#13)

> **Context:** Each phase subagent cold-starts and re-discovers context from large artifact files. Compact per-phase output manifests let later phases get context from small summaries instead of re-parsing large files.

> **Design decision (from review):** v1 used a single accumulating `phase-handoff.json` — shared mutable state that's fragile during retries and parallel runs. v2 uses immutable per-phase artifacts with schema versioning.

> **Effort:** 3-4 hours. **Savings:** ~$3-5/run (less if caching is active). **ROI:** Medium.

**Files:**
- Modify: `commands/cli-generation.md` (add per-phase output writes after each phase verification)

- [ ] **Step 1: Define phase artifact schema**

Each phase writes an immutable output manifest after completion. Schema:

```json
{
  "schema_version": 1,
  "phase": "<phase_name>",
  "run_id": "<pipeline run ID>",
  "timestamp": "<ISO 8601>",
  "source_artifacts": ["<list of input files this phase read>"],
  "outputs": {}
}
```

File naming convention: `.cli-pipeline/phase-outputs/phase-NN-<name>.json`

- [ ] **Step 2: Add Phase 0 output artifact**

In `commands/cli-generation.md`, after Step 0.7 (Initialize Pipeline Status), add:

````markdown
### Step 0.7b: Write Phase 0 Output Manifest

Write `.cli-pipeline/phase-outputs/phase-00-init.json`:

```json
{
  "schema_version": 1,
  "phase": "init",
  "run_id": "<generated UUID>",
  "timestamp": "<ISO 8601>",
  "source_artifacts": [".cli-pipeline/input-classification.json"],
  "outputs": {
    "cli_name": "<chosen-name>",
    "repo_path": "<absolute-path>",
    "tech_stack": "<typescript|python|powershell>",
    "input_type": "<classified type>"
  }
}
```

This file is immutable once written. Later phases read it but never modify it.
````

- [ ] **Step 3: Add Phase 1-8 output artifacts**

After each phase verification in `commands/cli-generation.md`, add a write step for the phase output manifest:

- **Phase 1 (auth-recon):** `.cli-pipeline/phase-outputs/phase-01-auth.json`
  ```json
  { "outputs": { "auth_type": "<type>", "credential_source": "<source>", "discovery_method": "<method>" } }
  ```

- **Phase 2 (api-recon):** `.cli-pipeline/phase-outputs/phase-02-api.json`
  ```json
  { "outputs": { "endpoint_count": "N", "resource_groups": ["..."], "base_url": "<url>", "spec_source": "<source>" } }
  ```

- **Phase 3 (validation):** `.cli-pipeline/phase-outputs/phase-03-validation.json`
  ```json
  { "outputs": { "valid": "N", "invalid": "N", "unreachable": "N", "auth_blocked": "N", "skipped_destructive": "N" } }
  ```

- **Phase 4 (architect):** `.cli-pipeline/phase-outputs/phase-04-architect.json`
  ```json
  { "outputs": { "command_count": "N", "helper_count": "N", "resource_groups": ["..."] } }
  ```

- **Phase 5 (arch audit):** `.cli-pipeline/phase-outputs/phase-05-arch-audit.json`
  ```json
  { "outputs": { "grade": "<letter>", "score": "N", "iterations": "N" } }
  ```

- **Phase 6 (generator):** `.cli-pipeline/phase-outputs/phase-06-generator.json`
  ```json
  { "outputs": { "source_files": "N", "test_files": "N", "tests_passed": "N" } }
  ```

- **Phase 7 (impl audit):** `.cli-pipeline/phase-outputs/phase-07-impl-audit.json`
  ```json
  { "outputs": { "grade": "<letter>", "score": "N", "tests_passed": "N", "tests_failed": "N", "iterations": "N" } }
  ```

- **Phase 8 (ideation):** `.cli-pipeline/phase-outputs/phase-08-ideation.json`
  ```json
  { "outputs": { "total_features": "N", "p0_count": "N", "p1_count": "N" } }
  ```

Read only the minimal fields needed from each phase's primary artifact (first 10-20 lines). Do NOT load full files.

- [ ] **Step 4: Update dispatch prompts to reference phase outputs**

For each phase dispatch (Phases 4-9) in `commands/cli-generation.md`, add to the dispatch prompt:

```
> Also read the relevant `.cli-pipeline/phase-outputs/phase-NN-*.json` files for compact summaries of prior phases.
> Use these for context instead of re-reading large artifact files when possible.
```

- [ ] **Step 5: Add schema validation instruction to orchestrator**

After reading each phase output, the orchestrator should validate:
- `schema_version` is recognized
- Required fields are present
- If validation fails, log a warning and fall back to reading the full artifact

- [ ] **Step 6: Verify changes**

```bash
cd ~/repos/cli-generation
grep -c "phase-outputs" commands/cli-generation.md
```
Expected: At least 10 references (1 init + 8 phase writes + dispatch references).

- [ ] **Step 7: Run quality gate**

Run pipeline on Medium API golden input. Verify later phases still produce correct output when reading summaries instead of full artifacts.

- [ ] **Step 8: Commit**

```bash
cd ~/repos/cli-generation
git add commands/cli-generation.md
git commit -m "perf: add immutable per-phase output artifacts (#13)

Orchestrator writes compact, immutable output manifests after each
phase (phase-outputs/phase-NN-*.json). Later phases read these
~200-500 token summaries instead of re-parsing large artifacts.
Schema-versioned for forward compatibility."
```

---

### Task 5: Break CLI Generator into Per-Resource Parallel Subagents (#11)

> **Context:** This is the most complex task. The CLI Generator (Phase 6) currently runs as a single agent writing 30+ command files sequentially. The proposal is to split it into a coordinator that writes shared modules first, then spawns per-resource subagents in parallel.

> **Effort:** 6-8 hours. **Savings:** ~$10-15/run. **ROI:** Medium.

**Files:**
- Modify: `agents/cli-generator.md` (restructure to coordinator + resource worker pattern)
- Modify: `commands/cli-generation.md:293-308` (Phase 6 dispatch section)

- [ ] **Step 1: Redesign cli-generator.md as a coordinator**

Replace the content of `agents/cli-generator.md` (keeping frontmatter) with:

````markdown
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
  - Agent
---

You are the cli-generator subagent in the cli-generation pipeline. Your job is to write the full CLI implementation using Test-Driven Development. This is the largest phase — you produce working, tested code, not scaffolding.

## Inputs

1. Read `<repo_path>/docs/architecture.md` — the full CLI design to implement
2. Read `.cli-pipeline/validated-endpoints.json` — endpoint details, schemas, auth requirements
3. Read `.cli-pipeline/input-classification.json` — `repo_path`, `tech_stack`, `cli_name`

If this agent receives an `audit-findings` parameter (dispatched by orchestrator after a Phase 7 retry), also read `<repo_path>/docs/impl-audit.md` for targeted fixes. In that case: do NOT regenerate — only fix what the audit identified, making surgical edits to existing files.

## Execution (Initial Generation)

1. Read all three input files.

2. **MUST invoke** `superpowers:test-driven-development` — follow the TDD cycle for every feature: write test → run test (expect fail) → implement → run test (expect pass) → refactor.

3. Scaffold the project based on `tech_stack`:

   **TypeScript:**
   - `package.json` with Commander.js, Vitest, tsup
   - `tsconfig.json`
   - `src/cli.ts` (main entry), `src/commands/`, `src/lib/` (http, auth, output, errors)
   - `tests/` (Vitest test files)
   - `.env.example`

   **Python:**
   - `pyproject.toml` with Click, pytest, httpx; use `uv` for environment management
   - `src/<cli_name>/cli.py` (entry point), `src/<cli_name>/commands/`, `src/<cli_name>/lib/`
   - `tests/` (pytest files)
   - `.env.example`

   **PowerShell:**
   - `<cli_name>.psd1` (module manifest), `<cli_name>.psm1` (root module)
   - `commands/` (one `.ps1` per resource), `lib/` (http.ps1, auth.ps1, output.ps1, errors.ps1)
   - `tests/` (Pester test files)
   - `.env.example`

4. Implement **shared modules first** (Phase A — sequential, in this agent):
   1. **Core lib**: HTTP client (retry, pagination, timeouts), auth module (credential chain), output formatter (JSON/table/yaml/csv), error types
   2. **Auth commands**: login, logout, status, and whoami (per architecture.md design)
   3. Run all tests to verify shared modules work.

5. **Decide parallelization strategy:**
   - Count the number of resource groups in `validated-endpoints.json` (using `tags`).
   - If **≤ 5 resource groups**: implement all commands sequentially in this agent (skip to step 7).
   - If **> 5 resource groups**: proceed to step 6 for parallel dispatch.

6. **Parallel resource dispatch** (Phase B — only for > 5 resource groups):

   Group endpoints by their `tags` field from `validated-endpoints.json`. For each resource group, dispatch a subagent using the Agent tool:

   ```
   Agent({
     description: "Generate <resource> commands",
     prompt: "You are generating CLI commands for the <resource> resource group.

   Read these files for context:
   - <repo_path>/docs/architecture.md (the CLI design — find the <resource> section)
   - .cli-pipeline/validated-endpoints.json (find endpoints with tag '<resource>')
   - .cli-pipeline/input-classification.json (tech_stack, cli_name)
   - <repo_path>/src/<cli_name>/client.py (or equivalent — the shared HTTP client)
   - <repo_path>/src/<cli_name>/auth.py (or equivalent — the shared auth module)
   - <repo_path>/src/<cli_name>/types.py (or equivalent — shared types)
   - <repo_path>/src/<cli_name>/errors.py (or equivalent — shared error types)

   Use superpowers:test-driven-development.

   Generate ONLY:
   - <repo_path>/src/<cli_name>/commands/<resource>_cmd.py (or .ts/.ps1)
   - <repo_path>/tests/test_commands/test_<resource>_cmd.py (or equivalent)

   For each endpoint with tag '<resource>':
   - Map operation_id to command name
   - Generate flags from params.query, params.path, and request_body
   - Wire output to JSON envelope format ({ status, data, metadata })
   - Every write/delete command gets --dry-run and --yes/--force guards
   - Import shared modules from the lib/ directory

   Run tests after implementation. All tests must pass.

   Return ONLY this JSON as your final message:
   {\"resource\": \"<resource>\", \"commands\": <N>, \"tests\": <N>, \"status\": \"passed\"}"
   })
   ```

   Dispatch up to 4 resource groups in parallel (to stay within reasonable concurrent agent limits). Wait for all to complete before dispatching the next batch.

7. **Sequential resource implementation** (only if ≤ 5 resource groups or audit-fix mode):

   For each resource group, implement commands sequentially following TDD:
   - Map `operation_id` to command name
   - Generate flags from `params.query`, `params.path`, and `request_body`
   - Wire output to JSON envelope format
   - Every write/delete command gets `--dry-run` and `--yes`/`--force` guards

8. **MUST invoke** `superpowers:verification-before-completion` before declaring done:
   - All tests pass
   - CLI builds and produces a runnable binary (or importable module)
   - `--help` works on every command
   - `--dry-run` works on every write command
   - JSON output is valid for all commands
   - Exit codes match the 0-5 contract

## Output

Writes to `<repo_path>/src/`, `<repo_path>/tests/`, `<repo_path>/package.json` (or equivalent).
The CLI repo must be buildable and all tests passing before this agent exits.

## Return Summary

Your final message back to the orchestrator MUST be ONLY this compact JSON (no prose, no explanation):

```json
{
  "schema_version": 1,
  "phase": "cli_generator",
  "status": "completed",
  "artifact": "<repo_path>/src/",
  "summary": "<one sentence: N source files, M test files, all tests passing>",
  "test_result": "<N passed, 0 failed>",
  "warnings": []
}
```
````

- [ ] **Step 2: Verify Agent tool in frontmatter**

```bash
cd ~/repos/cli-generation && head -15 agents/cli-generator.md
```
Expected: `tools` list includes `Agent`.

- [ ] **Step 3: Run quality gate**

Run pipeline on Large SDK golden input (the one with >5 resource groups). Compare generated CLI output against baseline golden files.

- [ ] **Step 4: Commit**

```bash
cd ~/repos/cli-generation
git add agents/cli-generator.md
git commit -m "perf: add parallel resource dispatch to CLI generator (#11)

For CLIs with >5 resource groups, the generator now spawns per-resource
subagents in batches of 4. Shared modules (client, auth, types, errors)
are still built sequentially first. Caps per-subagent context at ~30K
tokens vs 120K+ for the monolithic approach."
```

---

### Wave 3 Gate (Final)

- [ ] Measure total cumulative savings across all waves
- [ ] Compare all 3 golden inputs against baseline
- [ ] Document actual savings waterfall with real numbers
- [ ] Update GitHub issues with final results

---

## Savings Waterfall (Sequential, Not Additive)

> **Important:** These estimates are sequential — each row assumes all previous rows are already applied. Actual numbers will be filled in as each wave completes.

| Wave | Task | Baseline at this point | Estimated savings | New baseline | Actual (fill in) |
|---|---|---|---|---|---|
| 1 | Task 1: Prompt Caching | $184 | $0-80 (unknown) | $104-184 | _pending_ |
| 1 | Task 4: Sonnet Audits | $104-184 | ~$16 | $88-168 | _pending_ |
| 2 | Task 3: Return Summaries | $88-168 | ~$5-12 (depends on caching) | $76-163 | _pending_ |
| 2 | Task 6: Canonical Checklist | $76-163 | ~$3-6 (depends on caching) | $70-160 | _pending_ |
| 3 | Task 7: Phase Artifacts | $70-160 | ~$2-4 (depends on caching) | $66-158 | _pending_ |
| 3 | Task 5: Parallel Generator | $66-158 | ~$8-12 | $54-150 | _pending_ |

**Conservative target:** $80-110/run (if caching works moderately well)
**Pessimistic target:** $130-150/run (if caching is unavailable)
**Optimistic target:** $54-70/run (if caching delivers >70% hit rate)

---

## Removed Tasks

### ~~Task 2: Slim Orchestrator System Prompt (#8)~~ — REMOVED

**Reason:** Adding a preamble that tells the LLM to "ignore" context does NOT reduce billed tokens. The harness still sends MEMORY.md, rules.md, persona, and other files — you pay for every token whether the prompt says "ignore this" or not. The preamble actually *increases* cost by adding more tokens.

**What would work instead:** Harness-level changes to exclude non-pipeline files from context assembly, or a pipeline-specific system prompt that physically doesn't contain the daily-ops content. This requires platform changes outside the scope of this plan. Filed as a separate investigation.

### ~~Task 8: Skip Endpoint Validation for SDK-Based Inputs (#14)~~ — REMOVED

**Reason:** SDK method signatures do NOT guarantee endpoint correctness, auth scope correctness, version alignment, serialization behavior, or CLI usability. Skipping validation saves $3-4/run with unbounded downside. One bad CLI output costs orders of magnitude more in debugging time.

**Decision:** Keep full validation for all input types. The $3-4 savings is cheap insurance.

---

## Review Decisions

Decisions from the 3-model Principal Engineer review (2026-04-13):

| # | Finding | Consensus | Decision |
|---|---------|-----------|----------|
| 1 | Savings math double-counts | ALL 3 | ✅ Rework as sequential waterfall |
| 2 | Task 2 preamble can't reduce billed tokens | ALL 3 | ✅ Remove Task 2 entirely |
| 3 | Task 8 skips correctness for $3-4 | ALL 3 | ✅ Keep full validation |
| 4 | Task 1 must spike first | ALL 3 | ✅ Spike first, then re-estimate |
| 5 | No quality regression plan | ALL 3 | ✅ Golden files for 3 inputs |
| 6 | Tasks aren't independent | ALL 3 | ✅ Reframe as 3 workstreams |
| 7 | Handoff shared mutable state | ALL 3 | ✅ Immutable per-phase artifacts |
| 8 | Task 5 parallelism may increase tokens | GPT+Goldeneye | ❌ Dismissed — design is sound |
| 9 | Return summary schema too thin | GPT only | ⚡ Partial — add schema_version + warnings[] |
| 10 | Inline checklist = shotgun surgery | GPT only | ✅ Keep canonical reference |
| 11 | No effort/ROI estimates | Opus only | ✅ Add effort vs. savings matrix |

---

## Post-Implementation Verification

After all waves are complete:

- [ ] **Verify no file conflicts**

```bash
cd ~/repos/cli-generation
git log --oneline -10
git diff HEAD~6 --stat
```

- [ ] **Verify all agent frontmatter is valid**

```bash
cd ~/repos/cli-generation
for f in agents/*.md; do
  echo "=== $(basename $f) ==="
  awk '/^---$/{n++; if(n==2) exit} n>=1{print}' "$f"
done
```

- [ ] **Final golden file comparison**

Run pipeline on all 3 representative inputs. Compare against baseline golden files. Document:
- Cost per run (actual vs. estimated)
- Quality delta (grade changes, missing commands, broken tests)
- Token breakdown per phase

- [ ] **Update GitHub issues with final results**

Close each issue (#7, #9, #10, #11, #12, #13) with actual measured savings and quality results.