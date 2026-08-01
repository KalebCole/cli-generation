# Website-to-spec artifact contract

Each run lives under `.cli-pipeline/runs/<slug>/`.

| Artifact | Producer | Consumer | Commit? |
|---|---|---|---|
| `run.json` | `website_to_spec.py` | orchestrator | yes |
| `reachability.json` | Printing Press probe | recon + generator | yes |
| `use-cases.md` | recon agent + user approval | browser capture | yes |
| `capture.har` | browser/DevTools | Printing Press browser-sniff | no |
| `<slug>.yaml` | Printing Press browser-sniff | Printing Press generate | yes |
| `traffic-analysis.json` | Printing Press browser-sniff | generation/audit | yes, after redaction check |
| `samples/` | Printing Press browser-sniff | verification | no by default |
| `dry-run.json` | Printing Press generate | orchestrator | yes |

## `run.json` status values

- `probing`
- `capture_required`
- `spec_needs_review`
- `spec_validated`
- `failed`

`spec_needs_review` means the capture parsed, but semantic quality checks found an unusable endpoint model. Generation is withheld until the capture or spec is corrected.

`spec_validated` means the spec passed semantic checks and Printing Press dry-run. It does not mean the generated CLI has been built, dogfooded, or published.

## Secret boundary

Durable artifacts may describe:

- auth type
- header/cookie key name
- credential source reference
- runtime import/refresh strategy

They must not contain:

- access or refresh tokens
- cookie values
- authorization header values
- passwords
- payment data
- unrelated private response bodies
