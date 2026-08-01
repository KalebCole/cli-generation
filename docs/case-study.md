# Website-to-CLI reconnaissance case study

## Problem

Printing Press can generate and validate an agent-native Go CLI once it has a trustworthy API spec. Undocumented web apps do not provide that input. The hard part is working out which user flows matter, capturing the requests behind them, separating API traffic from browser noise, and refusing plausible but unusable specs.

The first version of `cli-generation` duplicated the generator. Version 2 removes that code and owns only the intake boundary.

## Workflow

```text
website
  -> infer user outcomes
  -> one approval checkpoint
  -> capture read-only browser traffic
  -> classify transport and auth
  -> emit Printing Press YAML
  -> semantic quality gate
  -> Printing Press dry-run
  -> generated Go CLI
  -> tests, security scan, live request
```

The agent stops only for final flow approval, login, or sensitive/write actions. Everything else is derived from evidence and recorded in a resumable run manifest.

## Live validation

### Open-Meteo success path

Target: `https://open-meteo.com/`

The browser fetched the same forecast flow for Seattle, New York, and Los Angeles. The resulting HAR contained three real API requests to `api.open-meteo.com`.

Observed handoff:

- 3 HAR requests
- 1 normalized endpoint: `GET /v1/forecast`
- 3 inferred flags: `--latitude`, `--longitude`, `--current`
- no authentication
- Printing Press dry-run: 1 resource, 1 endpoint
- generated Go test suite: passed
- `govulncheck`: no reachable vulnerabilities after updating `golang.org/x/text` from `v0.38.0` to `v0.39.0` in the disposable generated artifact
- compiled CLI returned live Seattle weather JSON

Evidence:

- [`spec.yaml`](evidence/open-meteo/spec.yaml)
- [`dry-run.json`](evidence/open-meteo/dry-run.json)
- [`traffic-analysis.json`](evidence/open-meteo/traffic-analysis.json)
- [`runtime-output.json`](evidence/open-meteo/runtime-output.json)

### HN Algolia rejection path

Target: `https://hn.algolia.com/`

The browser captured a real search and pagination flow. Printing Press's parser accepted the YAML, but Algolia's form-encoded JSON body became two giant CLI parameter names. A dry-run alone would have labeled that spec valid.

The wrapper now detects JSON documents emitted as parameter names, records `spec_needs_review`, withholds the generation command, and exits `3`.

Evidence:

- [`rejected-spec.yaml`](evidence/hn-quality-gate/rejected-spec.yaml)
- [`run.json`](evidence/hn-quality-gate/run.json)

## What this proves

- Recon and generation are separate contracts.
- Syntactic validation is insufficient for captured browser APIs.
- A failed real-site run improved the quality gate instead of being hidden.
- The successful path ends in a compiled CLI making a real request, not a mock or a generated-code screenshot.

## Known upstream issue

On August 1, 2026, Printing Press generated a module with `golang.org/x/text v0.38.0`. `govulncheck` reported GO-2026-5970 and identified `v0.39.0` as the fixed version. The generated test artifact was upgraded before runtime verification. This repository does not patch Printing Press's dependency template.
