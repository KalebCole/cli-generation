---
name: cli-generation
description: >-
  Turn a website or API surface into a validated Printing Press spec and generated CLI.
  Automates user-flow inference, auth/API reconnaissance, browser traffic analysis,
  replayability checks, and the handoff to cli-printing-press. Pauses only for final
  use-case approval, login, or a sensitive/write action.
---

# /cli-generation

Convert the supplied website, docs URL, API spec, or capture into a production CLI through Printing Press. This project is the reconnaissance front end; it does not reimplement Printing Press generation.

## Input

The command argument is one of:

- Website/web-app URL
- OpenAPI/Swagger URL or local file
- HAR/enriched-capture file plus target URL
- API documentation URL

If no input is supplied, ask for the target URL. Otherwise, do not ask for name, repo path, stack, or output directory. Derive sensible defaults and show them in the final report.

## Runtime contract

Use `.cli-pipeline/runs/<slug>/` as durable state. Never put raw cookies, authorization headers, or tokens there. Artifacts:

- `run.json`: compact resumable state
- `reachability.json`: Printing Press transport probe
- `use-cases.md`: approved user flows and capture boundary
- `capture.har`: optional local input; never commit it
- `<slug>.yaml`: Printing Press internal/OpenAPI spec
- `traffic-analysis.json`: redacted endpoint evidence
- `dry-run.json`: generator validation output

Add capture files, samples, and raw responses to `.gitignore`.

## Phase 0: Resume and classify

1. Look for `.cli-pipeline/runs/*/run.json` matching the target.
2. Resume the first incomplete phase automatically. Start fresh only when the user explicitly says so.
3. For a spec input, skip website reconnaissance and hand it directly to Printing Press dry-run validation.
4. For a website URL, continue below.

## Phase 1: Infer and approve user flows

1. Inspect public page content, navigation, documentation, metadata, and obvious product purpose.
2. Infer the top three workflows an agent would actually need. Each workflow must be phrased as a user outcome and expanded into concrete UI actions.
3. Classify every action:
   - `read-only`: safe to exercise automatically
   - `reversible-write`: requires explicit approval immediately before execution
   - `irreversible/sensitive`: do not execute during recon unless the user explicitly requests it
4. Present one compact approval checkpoint containing the proposed top three workflows and boundary. The user may approve or edit. This is the required final use-case approval.
5. Save the result to `use-cases.md`.

Do not ask about implementation details. Do not make the user choose browser backends, transport tiers, tech stacks, or endpoint groups.

## Phase 2: Passive recon and reachability

Run in parallel where possible:

1. `cli-printing-press probe-reachability <url> --json`
2. Search for official OpenAPI/Swagger, GraphQL schema, SDK, API docs, `.well-known` metadata, Next.js/SSR hydration, JSON-LD, and public feeds.
3. Inspect loaded scripts and public source references for endpoint hints only when structured sources are absent.
4. Identify whether the approved workflows require authentication.

Prefer, in order:

1. Official spec
2. Official SDK/schema/docs
3. Replayable API traffic
4. Structured SSR/HTML/feed extraction
5. HOLD if only resident browser execution works

Transport selection is automatic from the probe. Never ask the user to choose standard HTTP vs Surf/browser HTTP.

## Phase 3: Browser/API recon

Load and follow the `cli-site-recon` skill.

For website traffic:

1. Capture the approved read-only workflows in the user's existing authenticated browser when available.
2. If authentication is needed and no active session exists, stop once and ask the user to log in. Never ask for a password or token.
3. Install capture/interception before SPA interactions. Use click-based navigation so interceptors survive.
4. Record requests and responses needed by the workflows: URL, method, sanitized headers, query/body shape, response shape, pagination, and auth mechanism reference.
5. Compare public and authenticated sets.
6. Do not execute write, purchase, message-send, delete, account-change, or payment actions without explicit approval immediately before that action. A preview/dry-run is preferred.
7. Require replayability outside live page context. Classify every candidate as replayable, clearance-cookie replayable, structured extraction, or HOLD.

If a HAR/enriched capture already exists, skip browser driving and ingest it directly.

## Phase 4: Automated spec handoff

For browser traffic, run:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/website_to_spec.py" <url> \
  --name <slug> \
  --har <capture.har> \
  --run-dir .cli-pipeline/runs/<slug>
```

This command performs the deterministic handoff:

1. Reachability probe
2. `cli-printing-press browser-sniff`
3. Native YAML spec emission
4. `cli-printing-press generate --dry-run --json`
5. Resumable `run.json` update

For official specs, run Printing Press directly:

```bash
cli-printing-press generate --spec <spec> --spec-source official --dry-run --json
```

Do not manually translate a valid OpenAPI document into the internal YAML format.

## Phase 5: Generate and verify

Once dry-run validation succeeds, execute the `handoff_command` from `run.json`, adding an explicit output directory when appropriate. Then:

1. Build generated CLI.
2. Run generated tests.
3. Run `cli-printing-press dogfood` and `cli-printing-press scorecard`.
4. Exercise at least one approved workflow against the real service or a faithful replay fixture.
5. If verification fails, fix the spec/evidence first. Do not patch generated code to hide a bad surface model.

## Completion

Report only:

- Target and approved workflows
- Discovery source and endpoint count
- Auth mechanism reference, never credential values
- Spec path and generated CLI path
- Replayability/verification result
- Any HOLD items or sensitive workflows not exercised

The deliverable is a generated, exercised CLI plus the evidence/spec artifacts. A plan or dry-run alone is not completion.
