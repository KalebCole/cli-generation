---
name: cli-site-recon
version: 1.0.0
description: >-
  Reconnoiter a website for a Printing Press CLI. Infers outcome-oriented user flows,
  captures browser/API traffic, discovers auth without storing secrets, proves endpoint
  replayability, and emits evidence suitable for cli-printing-press browser-sniff.
allowed-tools:
  - Read
  - Write
  - Bash
  - WebFetch
  - WebSearch
  - Agent
  - AskUserQuestion
---

# CLI Site Recon

Use for a website or SPA with no complete public API specification. Goal: produce a small, evidence-backed, replayable surface for the approved workflows, not exhaustively mirror every network call.

## Human checkpoint policy

Exactly these conditions justify interruption:

1. **Final use-case approval:** Present inferred top workflows once before capture.
2. **Login:** Ask user to authenticate in a browser window when no valid session exists. Never request or type credentials.
3. **Sensitive/write action:** Ask immediately before any action that creates, modifies, sends, purchases, deletes, or exposes private data.

Everything else is autonomous. Backend choice, transport classification, names, paths, capture tooling, endpoint grouping, and validation are implementation details.

## Workflow

### 1. Establish intent

Inspect the site and infer up to three high-value outcomes. Turn each into an action sequence that forces lazy API calls to fire. Mark a stop boundary before the first sensitive/write action.

Save approved flows as:

```markdown
# Approved flows

## 1. Find an item
- Load search
- Enter query
- Open one result
- Stop boundary: before save/purchase/send
```

### 2. Find the lightest source

Check official spec, SDK, docs, GraphQL metadata, SSR hydration, embedded JSON, feeds, and browser traffic in that order. Run Printing Press reachability probe before browser escalation.

Do not browser-sniff when an official spec fully covers approved workflows. Do browser-sniff to fill only concrete gaps.

### 3. Capture safely

Preferred capture order:

1. Existing browser session via CDP/browser tooling
2. Browser automation with user login when required
3. User-exported HAR

Install interception before SPA navigation. Use clicks after interceptor installation. Capture only necessary calls. Redact authorization, cookies, tokens, email addresses, addresses, payment data, and unrelated account content from durable artifacts.

Never commit raw HAR files or browser profiles.

### 4. Model auth by reference

Record mechanism, not value:

```json
{
  "type": "cookie",
  "source": "existing_browser_session",
  "runtime_strategy": "browser_cookie_import",
  "secret_persisted": false
}
```

If an authorization header is constructed from a cookie/local-storage value, record scheme and source key name, never the value.

### 5. Prove replayability

A captured call enters the spec only if it works through one of:

- Standard HTTP client
- Browser-fingerprint HTTP transport
- Imported clearance/session cookie plus lightweight HTTP replay
- Structured HTML/SSR/RSS/JSON-LD extraction

Retry representative calls outside page context. A browser-only JavaScript execution path is `HOLD`, not an endpoint.

For writes, replay only with explicit approval and prefer sandbox, preview, or dry-run endpoints.

### 6. Emit Printing Press artifacts

When capture is HAR/enriched JSON:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/website_to_spec.py" <url> --har <capture> --run-dir <run-dir>
```

The script writes reachability, spec, traffic analysis, samples, dry-run output, and a resumable manifest. The generated `handoff_command` is the authoritative next command.

## Quality bar

Recon is complete when:

- Every approved read-only workflow maps to at least one validated command path
- Every emitted endpoint has evidence and a replayability class
- Public vs auth-required endpoints are distinguished
- Auth is modeled without persisted secrets
- Printing Press dry-run succeeds
- Unsupported/sensitive gaps are explicitly HOLD, not guessed
