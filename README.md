# cli-generation

A reconnaissance front end for [Printing Press](https://printingpress.dev).

Give it a website. It works out which user flows matter, captures the API traffic behind those flows, proves the calls can run outside the page, and hands a validated spec to Printing Press.

Printing Press remains the generator. This project handles the messy part before generation: deciding what the CLI should do and turning an undocumented web app into evidence that the generator can trust.

## What changed

The original version tried to build its own generator. That was the wrong boundary. Printing Press already generates, builds, audits, and packages agent-native Go CLIs better than this project did.

The useful missing piece was intake:

- infer outcome-oriented user flows from a website
- discover public and authenticated API surfaces
- capture only the traffic needed by those flows
- stop for login or sensitive actions without making every step manual
- reject endpoints that only work inside a live page
- emit Printing Press's native YAML spec and traffic analysis

The old implementation is preserved in [`docs/archive/cli-generation-v1.md`](docs/archive/cli-generation-v1.md).

## Run it

From Claude Code after installing the plugin:

```text
/cli-generation https://example.com
```

For an existing HAR or enriched capture:

```bash
python3 scripts/website_to_spec.py https://example.com \
  --har ~/Downloads/example.har \
  --run-dir .cli-pipeline/runs/example
```

The script runs:

1. `cli-printing-press probe-reachability`
2. `cli-printing-press browser-sniff`
3. a semantic quality gate for malformed captured parameters
4. `cli-printing-press generate --dry-run`

On success, `run.json` contains the exact handoff command for full generation. See the [live Open-Meteo and HN Algolia case study](docs/case-study.md) for both the success and rejection paths.

## Human checkpoints

The workflow interrupts only when judgment or consent is necessary:

- approve the final user-flow plan
- log in when no valid browser session exists
- approve a write, purchase, message, deletion, or other sensitive action

Names, output paths, capture tooling, transport, auth classification, endpoint grouping, and validation are automatic.

## Artifacts

Each run lives in `.cli-pipeline/runs/<slug>/`.

| File | Purpose |
|---|---|
| `run.json` | resumable status and handoff command |
| `reachability.json` | transport probe result |
| `use-cases.md` | approved workflows and stop boundaries |
| `<slug>.yaml` | Printing Press spec |
| `traffic-analysis.json` | redacted endpoint evidence |
| `dry-run.json` | generator validation output |

Raw captures and samples stay out of git.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

The test suite uses a fake Printing Press binary and verifies the full probe, sniff, validate, and resume contract without touching a live account.

## Requirements

- Python 3.9+
- `cli-printing-press` 4.29+
- A supported browser capture path for undocumented sites: browser automation, CDP, or a HAR export

## Install

```bash
claude plugin marketplace add https://github.com/KalebCole/cli-generation.git
claude plugin install cli-generation@cli-generation-marketplace
```

## License

MIT
