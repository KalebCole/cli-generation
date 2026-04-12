# CLI Audit Quality Checklist

Source of truth for the 14-point grading system. Each check has a weight, verification method, and pass/partial/fail criteria.

## Checklist

### 1. JSON Output to stdout (Weight: 10)

**What:** Every command outputs valid JSON to stdout on every invocation.

**PASS:** JSON is the default output format. `--format table` is opt-in for humans. Stdout contains ONLY JSON.
**PARTIAL:** JSON available via `--json` flag, but default is unstructured text.
**FAIL:** Some commands output text-only. JSON corrupted by log messages on stdout.

**How to verify:**
```
grep -r "console.log\|process.stdout.write\|print(" src/commands/ --include="*.ts"
# Check: are ALL stdout writes going through a structured output function?
```

### 2. Exit Codes Match Contract (Weight: 5)

**What:** Exit codes follow a structured contract: 0=success, 1=api_error, 2=auth_error, 3=validation_error, 4=not_found, 5=internal_error.

**PASS:** All 5 error codes used appropriately. Auth failures exit 2, not 1.
**PARTIAL:** Exit codes defined but some are unused, or only 0/1 are used.
**FAIL:** Only exit 0 and exit 1 exist. No structured error typing.

**How to verify:**
```
grep -rn "process.exit\|sys.exit\|os.Exit" src/ --include="*.ts"
# Check: are exit codes from the contract? Is each code used at least once?
```

### 3. --help on Every Command (Weight: 5)

**What:** Every command and subcommand has `--help` with description, usage, flags, examples.

**PASS:** CLI framework auto-generates help. Every command has a description string.
**PARTIAL:** Help exists but some commands lack descriptions or examples.
**FAIL:** No help system, or manual `console.log("Usage: ...")`.

**How to verify:**
```
# Check CLI framework registration — Commander, Click, Cobra all auto-generate --help
# Verify each command has .description() or equivalent
```

### 4. --dry-run on Write/Delete Commands (Weight: 5)

**What:** Every command that modifies state supports `--dry-run` which shows what WOULD happen without doing it.

**PASS:** All write/delete commands have --dry-run. Dry run prints the request and exits 0.
**PARTIAL:** Some write commands have it, others don't.
**FAIL:** No --dry-run support anywhere. N/A if CLI is read-only.

**How to verify:**
```
grep -r "dry.run\|dryRun\|dry_run" src/ --include="*.ts"
# Check: does it actually prevent the API call, or just log?
```

### 5. --yes/--force on Destructive Commands (Weight: 5)

**What:** Destructive commands (delete, overwrite, cancel) prompt for confirmation unless `--yes` (skip prompt) or `--force` (skip prompt + overwrite protection) is passed.

**PASS:** All destructive commands prompt by default. Both --yes and --force work. Neither skips --dry-run.
**PARTIAL:** Some destructive commands prompt, but not all. Or only --yes exists.
**FAIL:** No confirmation prompts. Destructive actions execute immediately. N/A if no destructive commands.

### 6. --format Flag with Multiple Formats (Weight: 10)

**What:** Global `--format` flag supports json (default), table, yaml, csv.

**PASS:** `--format json` is default. Table, yaml, csv all produce valid output.
**PARTIAL:** `--json` boolean flag. Or only json+table supported.
**FAIL:** No format control. Output format varies by command.

### 7. Auth Follows Credential Precedence (Weight: 8)

**What:** Auth resolves in order: env var token → credentials file → interactive login → system credential.

**PASS:** Full precedence chain. Token env var works. Credentials file path configurable.
**PARTIAL:** Some tiers implemented (e.g., disk + interactive, but no env var).
**FAIL:** Single hardcoded auth method. No fallback chain.

### 8. HTTP Retry on 429/5xx (Weight: 8)

**What:** HTTP client retries transient failures with exponential backoff + jitter.

**PASS:** Retries 429 and 5xx. Respects Retry-After. Max 3 retries. Jitter applied. Never retries 4xx (except 429).
**PARTIAL:** Retries exist but missing jitter, or retries all errors, or doesn't respect Retry-After.
**FAIL:** No retry logic. First failure throws.

### 9. Pagination Auto-Paginates (Weight: 7)

**What:** List commands auto-paginate. Support `--page-size`, `--page-all` (NDJSON stream), `--page-limit`.

**PASS:** Auto-pagination with all flags. NDJSON streaming for `--page-all`.
**PARTIAL:** Pagination params exist in API client but not exposed as CLI flags.
**FAIL:** No pagination. Hardcoded `top: 50` or similar.

### 10. SKILL.md Files Exist — Layered (Weight: 8)

**What:** SKILL.md files organized by layer: shared, per-resource, per-helper.

**PASS:** Shared skill + at least one resource skill + at least one helper skill.
**PARTIAL:** Single monolithic SKILL.md file covering everything.
**FAIL:** No SKILL.md at all.

### 11. README Follows GWS Pattern (Weight: 5)

**What:** README includes: install, quick start, auth, command reference, exit codes, env vars, troubleshooting.

**PASS:** All 7 sections present with examples.
**PARTIAL:** Missing 1-3 sections (usually env vars, troubleshooting).
**FAIL:** Minimal README or no README.

### 12. No Secrets in Output/Logs (Weight: 8)

**What:** Tokens, passwords, API keys never appear in stdout, stderr, or log files.

**PASS:** Tokens redacted or never logged. Auth headers not printed even with --verbose.
**PARTIAL:** Tokens not in stdout but appear in --verbose debug output.
**FAIL:** Tokens logged to stdout or files.

### 13. Errors are JSON Objects (Weight: 8)

**What:** Error output is a JSON object with `code` (exit code int), `type` (error category string), and `message` (human string).

**PASS:** All errors use the envelope: `{ "status": "error", "error": { "code": 1, "type": "api_error", "message": "..." } }`
**PARTIAL:** JSON errors exist but missing `type` field, or inconsistent structure.
**FAIL:** Errors are plain strings or stack traces.

### 14. Tests Cover Key Areas (Weight: 8)

**What:** Tests exist for: CRUD operations, auth flow, HTTP retry, pagination, output format, exit codes.

**PASS:** Tests cover all 6 areas. CI runs them.
**PARTIAL:** Some tests exist but major gaps (e.g., no retry tests, no exit code tests).
**FAIL:** Zero tests, or test dirs exist but are empty.

## Category Groupings

| Category | Checks | Total Weight |
|----------|--------|-------------|
| Output Contract | 1, 6, 13 | 28 |
| Safety & Confirmation | 4, 5, 12 | 18 |
| Infrastructure | 7, 8, 9 | 23 |
| Documentation | 3, 10, 11 | 18 |
| Testing | 14 | 8 |
| Exit Codes | 2 | 5 |
| **Total** | | **100** |
