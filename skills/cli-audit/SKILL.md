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

# CLI Audit

Grade any CLI against the cli-architect quality checklist. Produces a scorecard with letter grade and a prioritized remediation backlog.

## When to Use

- You have a CLI and want to know how "agentic-ready" it is
- You want a structured gap analysis before improving a CLI
- You want to compare CLIs against a consistent standard
- You finished a build phase and want to validate quality

## Workflow

### Step 1: Scan the Codebase

Dispatch **1 explore agent** to comprehensively scan the CLI:

```prompt
Analyze the CLI codebase at {path}. For each of the following, report what you find:

1. OUTPUT: How does each command produce output? Is it JSON to stdout? Mixed text+JSON?
   Search for: console.log, process.stdout, print, Write-Output, fmt.Print
2. EXIT CODES: What exit codes are used? Search for: process.exit, sys.exit, os.Exit, exit
3. HELP: Does every command have --help? Check CLI framework registration.
4. DRY-RUN: Is there a --dry-run flag on write/delete commands? Search for: dry.run, dryRun
5. YES/FORCE: Are there --yes/--force flags on destructive commands? Search for: yes, force, confirm
6. FORMAT: Is there a --format flag? What output formats are supported?
7. AUTH: How does auth work? Is there a credential precedence chain?
8. RETRY: Does the HTTP client retry on 429/5xx? Search for: retry, backoff, exponential
9. PAGINATION: Is there auto-pagination? Search for: page, offset, cursor, next, limit
10. SKILLS: Do SKILL.md files exist? Are they layered (shared/resource/helper)?
11. README: Does README follow the GWS pattern? (install, quickstart, auth, commands, exit codes, env vars)
12. SECRETS: Are tokens/passwords ever logged? Search for: token, password, secret, key in log/print statements
13. ERRORS: Are errors JSON objects with code, type, message fields?
14. TESTS: What test coverage exists? Count test files, check what's tested.

Read every relevant file. Be thorough — a missed detail changes the score.
```

### Step 2: Evaluate Against Checklist

Score each of the 14 checks using the quality checklist in `references/quality-checklist.md`.

For each check, assign:
- **PASS** (100%) — Fully implemented, no gaps
- **PARTIAL** (50%) — Implemented but with issues
- **FAIL** (0%) — Not implemented
- **N/A** — Not applicable (excluded from total, explain why)

### Step 3: Calculate Score

```
Weighted Score = Σ (check_score × check_weight) / Σ (applicable_weights)

Letter Grade:
  A  = 90-100%
  B  = 80-89%
  C  = 70-79%
  D  = 60-69%
  F  = <60%

Add +/- modifiers:
  x7-x9 within range = +  (e.g., 87-89 = B+)
  x0-x3 within range = -  (e.g., 80-83 = B-)
```

### Step 4: Present Scorecard

```markdown
## CLI Audit: {name} — Grade: {grade} ({score}%)

### Scorecard

| # | Check | Weight | Status | Score | Notes |
|---|-------|--------|--------|-------|-------|
| 1 | JSON output to stdout | 10 | ⚠️ PARTIAL | 5/10 | --json opt-in, not default |
| 2 | Exit codes match contract | 5 | ❌ FAIL | 0/5 | Only uses 0 and 1 |
...

### Category Breakdown

| Category | Score | Max | Pct |
|----------|-------|-----|-----|
| Output Contract (1,6,13) | ... | 28 | ...% |
| Safety & Confirmation (4,5,12) | ... | 18 | ...% |
| Infrastructure (7,8,9) | ... | 23 | ...% |
| Documentation (3,10,11) | ... | 18 | ...% |
| Testing (14) | ... | 8 | ...% |
| Exit Codes (2) | ... | 5 | ...% |

### Top Remediation Items (sorted by point impact)

1. **[{weight} pts] {check_name}** — {what to fix}
2. ...
```

🛑 **STOP GATE** — User reviews scorecard. Options: fix gaps and re-audit, or proceed to ideation.

## Common Mistakes

- **Scoring --json flag as PASS for Check 1.** JSON-first means JSON is the DEFAULT. `--json` opt-in is PARTIAL at best.
- **Ignoring unused exit codes.** Defined but unused exit codes count as FAIL — they create a false contract.
- **Counting test files without reading them.** Empty test directories or skeleton tests with no assertions are FAIL.
- **Missing stderr contamination.** If ANY informational text goes to stdout alongside JSON, Check 1 is FAIL.
